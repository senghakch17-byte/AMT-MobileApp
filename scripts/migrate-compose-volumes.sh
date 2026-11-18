#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/migrate-compose-volumes.sh --dry-run
       ./scripts/migrate-compose-volumes.sh --execute

Copies event_uploads → announcement_uploads and member_uploads → user_uploads.
Source volumes remain intact for rollback. Stop the Compose stack before executing.
EOF
}

[[ $# -eq 1 && ( $1 == --dry-run || $1 == --execute ) ]] || { usage >&2; exit 2; }
execute=$([[ $1 == --execute ]] && echo true || echo false)

for pair in 'event_uploads announcement_uploads' 'member_uploads user_uploads'; do
  read -r source destination <<<"$pair"
  docker volume inspect "$source" >/dev/null 2>&1 || { echo "Missing source volume: $source" >&2; exit 1; }
  if [[ $execute == true ]]; then
    docker volume create "$destination" >/dev/null
    existing=$(docker run --rm -v "$destination":/destination alpine sh -c 'find /destination -mindepth 1 -print -quit')
    [[ -z $existing ]] || { echo "Destination volume is not empty: $destination" >&2; exit 1; }
    docker run --rm -v "$source":/source:ro -v "$destination":/destination alpine sh -c 'cp -a /source/. /destination/'
  fi
  echo "$source → $destination ($([[ $execute == true ]] && echo copied || echo dry-run))"
done
