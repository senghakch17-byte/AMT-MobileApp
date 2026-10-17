#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for service in api-gateway registration-service login-service attendance-service notification-service; do
  echo "=== Testing ${service} ==="
  (cd "${root_dir}/apps/${service}" && npm test)
done

for service in request-service event-service member-service library-service; do
  echo "=== Testing ${service} ==="
  (cd "${root_dir}/apps/${service}" && uv sync && uv run pytest)
done