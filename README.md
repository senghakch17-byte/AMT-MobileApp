# AMT Mobile App Backend

Containerized microservices backend for registration, login, attendance, leave requests, pre-scholarship registrations, and events.

## Architecture

Nginx on port `80` is public entry point. It load-balances requests between two API gateway replicas. Gateway debug ports are `4000` and `4001`.

```text
Mobile app
    |
    v
Nginx :80
    |
    v
API gateways :4000, :4001
    |-- /register  -> Registration service :5001
    |-- /auth      -> Login service :5002
    |-- /request   -> Request service :8000
    |-- /event     -> Event service :8001
    |-- /attendance -> Attendance service :8002
    `-- /notification -> Notification service :8005

All application services -> external MongoDB
Event service -> event_uploads volume
```

| Service | Compose service | Host port | Responsibility |
| --- | --- | ---: | --- |
| Nginx | `nginx` | 80 | Public entry point and gateway load balancer |
| API gateway 1 | `gateway1` | 4000 | Routing and JWT authentication |
| API gateway 2 | `gateway2` | 4001 | Routing and JWT authentication |
| Redis | `redis` | 6379 | Shared Redis service |
| Registration | `register` | 5001 | Account creation and password hashing |
| Login | `login` | 5002 | Credential validation and JWT issuance |
| Request | `request-service` | 8000 | Leave requests and pre-scholarship registrations |
| Event | `event-service` | 8001 | Event management and image storage |
| Attendance | `attendance-service` | 8002 | User check-in, check-out, history, and admin corrections |
| Notification | `notification-service` | 8005 | In-app notifications and user receipt state |

MongoDB is external; Compose does not provision it. Node services use `MONGO_URI`; Python services use `MONGODB_URI`.

## Current limitations

- `deploy/` contains incomplete EC2 Compose configuration that is not production-verified.
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
docker compose logs -f register login request-service event-service
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
- [Configuration](docs/CONFIGURATION.md)
- [Local development](docs/LOCAL_DEVELOPMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [AWS sandbox development](docs/AWS_DEVELOPMENT.md)
- [Postman collection](docs/postman/README.md)

## Local development

See [local development guide](docs/LOCAL_DEVELOPMENT.md).

## Repository layout

```text
apps/
  api-gateway/          Express gateway and JWT middleware
  registration-service/ Express registration API
  login-service/        Express login API and JWT issuance
  request-service/      FastAPI request APIs
  event-service/        FastAPI event API and uploads
  attendance-service/   Express attendance API
deploy/                 EC2 Docker Compose configuration
nginx/                  Nginx load balancer configuration
docs/                   API, configuration, development, and Postman docs
docker-compose.yaml     Local orchestration configuration
AGENTS.md               Agent and contribution instructions
README.md               Project setup and operations
```

## Troubleshooting

See [troubleshooting guide](docs/TROUBLESHOOTING.md).
