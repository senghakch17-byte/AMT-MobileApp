#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: MONGODB_URI='mongodb://...' ./scripts/empty-mongodb.sh --execute DATABASE_NAME

Deletes every document from every collection in DATABASE_NAME while preserving
collections and indexes. Requires --execute and typing DATABASE_NAME again.

Refuses system MongoDB databases: admin, config, local.
EOF
}

if [[ ${1:-} == '--help' || ${1:-} == '-h' ]]; then
  usage
  exit 0
fi

if [[ ${1:-} != '--execute' || $# -ne 2 ]]; then
  usage >&2
  exit 2
fi

if [[ -z ${MONGODB_URI:-} ]]; then
  echo 'MONGODB_URI is required.' >&2
  exit 2
fi

database=$2
if [[ ! $database =~ ^[A-Za-z0-9_.-]+$ ]]; then
  echo 'DATABASE_NAME may contain only letters, numbers, dot, underscore, and hyphen.' >&2
  exit 2
fi

case $database in
  admin|config|local)
    echo "Refusing protected MongoDB database: $database" >&2
    exit 2
    ;;
esac

echo "This permanently deletes all documents from MongoDB database: $database"
read -r -p "Type $database to continue: " confirmation
if [[ $confirmation != "$database" ]]; then
  echo 'Confirmation did not match. No documents deleted.' >&2
  exit 1
fi

MONGODB_CLEAN_DATABASE=$database mongosh "$MONGODB_URI" --quiet --eval '
const targetDb = db.getSiblingDB(process.env.MONGODB_CLEAN_DATABASE);
let deleted = 0;

for (const { name } of targetDb.getCollectionInfos({ type: "collection" })) {
  const result = targetDb.getCollection(name).deleteMany({});
  deleted += result.deletedCount;
  print(`${name}: deleted ${result.deletedCount}`);
}

print(`Total documents deleted: ${deleted}`);
'