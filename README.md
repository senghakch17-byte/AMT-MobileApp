# OMS Microservice Backend

Containerized OMS backend for registration, login, attendance, leave requests, announcements, notifications, user profiles, and room bookings.

## Architecture

Nginx on port `80` is the public entry point. It load-balances requests between two API gateway replicas, both listening on container port `4000`.

```text
Mobile app
    |
    v
Nginx :80
    |
    v
API gateways :4000 (container)
    |-- /register  -> Registration service :5001
    |-- /login     -> Login service :5002
    |-- /request   -> Request service :8000
    |-- /announcement     -> Event service :8001
    |-- /attendance -> Attendance service :8002
    |-- /notification -> Notification service :8005
    |-- /user    -> Member service :8004
    `-- /booking    -> Library service :8003

All application services -> external MongoDB
Event service -> announcement_uploads volume
```

| Service | Compose service | Host port | Responsibility |
| --- | --- | ---: | --- |
| Nginx | `nginx` | 80 | Public entry point and gateway load balancer |
| API gateway 1 | `gateway1` | — | Routing and JWT authentication through Nginx |
| API gateway 2 | `gateway2` | — | Routing and JWT authentication through Nginx |
| Redis | `redis` | 6379 | Shared Redis service |
| Registration | `register` | 5001 | Account creation and password hashing |
| Login | `login` | 5002 | Credential validation and JWT issuance |
| Request | `request-service` | 8000 | Leave requests and approval workflow |
| Announcement | `announcement-service` | 8001 | Announcement management and image storage |
| Attendance | `attendance-service` | 8002 | User check-in, check-out, history, and admin corrections |
| Booking | `booking-service` | 8003 | Room bookings and approval workflow |
| User | `user-service` | 8004 | User profiles and protected document history |
| Notification | `notification-service` | 8005 | In-app notifications and user receipt state |

MongoDB is external; Compose does not provision it. Node services use `MONGO_URI`; Python services use `MONGODB_URI`.

## Current limitations

- `deploy/` contains unverified EC2 Compose configuration. Four-host deployment needs real EC2 validation before course submission; see [AWS sandbox development](docs/AWS_DEVELOPMENT.md).
- FastAPI `root_path` values do not match gateway prefixes. Direct Swagger pages may generate incorrect URLs, and protected gateway docs may not load their schemas in a browser.

## Prerequisites

- Docker Desktop with Docker Compose
- Reachable MongoDB deployment
- Shared JWT secret for login, gateway, request, event, and attendance services
- Python 3.12 and `uv` for Python services outside Docker

## Configuration

See [configuration guide](docs/CONFIGURATION.md).

## Run with Docker Compose

Validate and start stack from repository root:

```bash
docker compose config
docker compose up --build
```

Useful commands:

```bash
docker compose up -d --build
docker compose logs -f api-gateway
docker compose logs -f register login request-service announcement-service
docker compose down
docker compose down -v # also removes event uploads
```

`depends_on` controls startup order, not readiness. No Compose health checks wait for MongoDB or upstream APIs.

## Empty local/test MongoDB data

`scripts/empty-mongodb.sh` deletes every document from every collection while preserving collections and indexes. It does not drop databases, collections, or indexes. Use only against an intended local/test database.

```bash
export MONGODB_URI='mongodb+srv://<username>:<password>@<cluster>.mongodb.net'
./scripts/empty-mongodb.sh --execute final_project
```

Script refuses MongoDB system databases and requires typing target database name before deletion.

## Tests

Run all service suites from repository root:

```bash
./test-all.sh
```

The script stops at first failure. Python suites run `uv sync` before `pytest`.

## Documentation

- [API contract](docs/API_CONTRACT.md)
- [Project documentation](docs/PROJECT_DOCUMENTATION.md)
- [Configuration](docs/CONFIGURATION.md)
- [Local development](docs/LOCAL_DEVELOPMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [AWS sandbox development](docs/AWS_DEVELOPMENT.md)
- [Postman collection](docs/postman/README.md)
- [Minikube Kubernetes manifests](deploy/k8s/README.md)

## Local development

See [local development guide](docs/LOCAL_DEVELOPMENT.md).

## Repository layout

```text
apps/
  api-gateway/          Express gateway and JWT middleware
  registration-service/ Express registration API
  login-service/        Express login API and JWT issuance
  request-service/      FastAPI request APIs
  announcement-service/        FastAPI event API and uploads
  attendance-service/   Express attendance API
  booking-service/      FastAPI room booking API
  user-service/       FastAPI user profile and document API
deploy/                 EC2 Docker Compose configuration
nginx/                  Nginx load balancer configuration
docs/                   API, configuration, development, and Postman docs
docker-compose.yaml     Local orchestration configuration
AGENTS.md               Agent and contribution instructions
README.md               Project setup and operations
```

## Troubleshooting

See [troubleshooting guide](docs/TROUBLESHOOTING.md).
