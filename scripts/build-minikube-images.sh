#!/usr/bin/env bash
set -euo pipefail

if ! minikube status --format '{{.Host}}' 2>/dev/null | grep -qx Running; then
  echo 'Start Minikube first: minikube start'
  exit 1
fi

declare -a images=(
  'oms-api-gateway:latest apps/api-gateway'
  'oms-registration-service:latest apps/registration-service'
  'oms-login-service:latest apps/login-service'
  'oms-request-service:latest apps/request-service'
  'oms-announcement-service:latest apps/announcement-service'
  'oms-attendance-service:latest apps/attendance-service'
  'oms-booking-service:latest apps/booking-service'
  'oms-user-service:latest apps/user-service'
  'oms-notification-service:latest apps/notification-service'
)

for entry in "${images[@]}"; do
  read -r image context <<<"${entry}"
  minikube image build -t "${image}" "${context}"
done
