#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/migrate-compose-volumes.sh --dry-run
       ./scripts/migrate-compose-volumes.sh --execute

Copies event_uploads → announcement_uploads and member_uploads → user_uploads.
It accepts either unprefixed volumes or the project-prefixed names Docker Compose
normally creates (for example, `amt-mobileapp_event_uploads`). Source volumes
remain intact for rollback. Stop the Compose stack before executing.
EOF
}

[[ $# -eq 1 && ( $1 == --dry-run || $1 == --execute ) ]] || { usage >&2; exit 2; }
execute=$([[ $1 == --execute ]] && echo true || echo false)

resolve_source_volume() {
  local logical_name=$1
  local matches=()
  local volume
  while IFS= read -r volume; do
    [[ -n $volume ]] && matches+=("$volume")
  done < <(docker volume ls -q | grep -E "(^|_)${logical_name}$" || true)

  if [[ ${#matches[@]} -eq 0 ]]; then
    echo "Missing source volume matching: $logical_name" >&2
    exit 1
  fi
  if [[ ${#matches[@]} -gt 1 ]]; then
    echo "Multiple source volumes match $logical_name: ${matches[*]}" >&2
    echo 'Remove ambiguity or migrate the intended volume manually.' >&2
    exit 1
  fi
  printf '%s\n' "${matches[0]}"
}

for pair in 'event_uploads announcement_uploads' 'member_uploads user_uploads'; do
  read -r source_logical destination_logical <<<"$pair"
  source=$(resolve_source_volume "$source_logical")
  destination="${source%"$source_logical"}$destination_logical"
  if [[ $execute == true ]]; then
    docker volume create "$destination" >/dev/null
    existing=$(docker run --rm -v "$destination":/destination alpine sh -c 'find /destination -mindepth 1 -print -quit')
    [[ -z $existing ]] || { echo "Destination volume is not empty: $destination" >&2; exit 1; }
    docker run --rm -v "$source":/source:ro -v "$destination":/destination alpine sh -c 'cp -a /source/. /destination/'
  fi
  echo "$source → $destination ($([[ $execute == true ]] && echo copied || echo dry-run))"
done
