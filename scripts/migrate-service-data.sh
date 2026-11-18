#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: MONGODB_URI='mongodb://...' ./scripts/migrate-service-data.sh --dry-run DATABASE
       MONGODB_URI='mongodb://...' ./scripts/migrate-service-data.sh --execute DATABASE

Renames events → announcements, members → user_profiles, and
member_documents → user_documents. It also changes notification eventId to
notificationKey and announcement notification terminology. Back up MongoDB first.
EOF
}

[[ $# -eq 2 && ( $1 == --dry-run || $1 == --execute ) ]] || { usage >&2; exit 2; }
[[ -n ${MONGODB_URI:-} ]] || { echo 'MONGODB_URI is required.' >&2; exit 2; }
database=$2
[[ $database =~ ^[A-Za-z0-9_.-]+$ ]] || { echo 'Invalid database name.' >&2; exit 2; }
case $database in admin|config|local) echo 'Refusing MongoDB system database.' >&2; exit 2;; esac

mode=$1
if [[ $mode == --execute ]]; then
  echo "Back up MongoDB before continuing. This migrates $database."
  read -r -p "Type $database to continue: " confirmation
  [[ $confirmation == "$database" ]] || { echo 'Confirmation did not match.' >&2; exit 1; }
fi

MONGODB_MIGRATION_DATABASE=$database MONGODB_MIGRATION_EXECUTE=$([[ $mode == --execute ]] && echo true || echo false) \
  mongosh "$MONGODB_URI" --quiet --eval '
const targetDb = db.getSiblingDB(process.env.MONGODB_MIGRATION_DATABASE);
const execute = process.env.MONGODB_MIGRATION_EXECUTE === "true";
const names = new Set(targetDb.getCollectionInfos({ type: "collection" }).map(({ name }) => name));
const renames = [["events", "announcements"], ["members", "user_profiles"], ["member_documents", "user_documents"]];
for (const [from, to] of renames) {
  if (names.has(from) && names.has(to)) throw new Error(`Both ${from} and ${to} exist; aborting.`);
}
print(`Mode: ${execute ? "EXECUTE" : "DRY RUN"}`);
for (const [from, to] of renames) {
  if (!names.has(from)) { print(`${from}: not present`); continue; }
  print(`${from} → ${to}`);
  if (execute) targetDb.getCollection(from).renameCollection(to);
}
const notifications = targetDb.getCollection("notifications");
if (names.has("notifications")) {
  const count = notifications.countDocuments({ eventId: { $exists: true } });
  print(`notifications eventId → notificationKey: ${count}`);
  if (execute) {
    for (const index of notifications.getIndexes()) {
      if (JSON.stringify(index.key).includes("eventId")) notifications.dropIndex(index.name);
    }
    notifications.updateMany({ eventId: { $exists: true } }, [{ $set: { notificationKey: "$eventId" } }, { $unset: "eventId" }]);
    notifications.updateMany({ type: "event.published" }, { $set: { type: "announcement.published" } });
    notifications.updateMany({ type: "event.updated" }, { $set: { type: "announcement.updated" } });
    notifications.updateMany({ "data.event_id": { $exists: true } }, [{ $set: { "data.announcement_id": "$data.event_id" } }, { $unset: "data.event_id" }]);
    notifications.updateMany({ notificationKey: /^event-service:/ }, [{ $set: { notificationKey: { $replaceOne: { input: "$notificationKey", find: "event-service:", replacement: "announcement-service:" } } } }]);
    notifications.createIndex({ recipientId: 1, notificationKey: 1 }, { unique: true, partialFilterExpression: { recipientId: { $type: "string" } } });
    notifications.createIndex({ recipientRole: 1, notificationKey: 1 }, { unique: true, partialFilterExpression: { recipientRole: { $type: "string" } } });
  }
}
const preferences = targetDb.getCollection("preferences");
if (names.has("preferences")) {
  const count = preferences.countDocuments({ mutedTypes: { $in: ["event.published", "event.updated"] } });
  print(`notification preferences to update: ${count}`);
  if (execute) preferences.updateMany({}, [{ $set: { mutedTypes: { $map: { input: { $ifNull: ["$mutedTypes", []] }, as: "type", in: { $switch: { branches: [{ case: { $eq: ["$$type", "event.published"] }, then: "announcement.published" }, { case: { $eq: ["$$type", "event.updated"] }, then: "announcement.updated" }], default: "$$type" } } } } }]);
}
print("Migration complete.");
'
