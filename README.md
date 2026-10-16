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
    `-- /attendance -> Attendance service :8002

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

MongoDB is external; Compose does not provision it. Node services use `MONGO_URI`; Python services use `MONGODB_URI`.

## Current limitations

- `deploy/` contains empty EC2 Compose placeholders and no deployable infrastructure.
- FastAPI `root_path` values do not match gateway prefixes. Direct Swagger pages may generate incorrect URLs, and protected gateway docs may not load their schemas in a browser.

## Prerequisites

- Docker Desktop with Docker Compose
- Reachable MongoDB deployment
- Shared JWT secret for login, gateway, request, event, and attendance services
- Python 3.12 and `uv` for Python services outside Docker

## Configuration

From repository root, copy each template and replace placeholder values:

```bash
cp apps/registration-service/.env.example apps/registration-service/.env
cp apps/attendance-service/.env.example apps/attendance-service/.env
cp apps/login-service/.env.example apps/login-service/.env
cp apps/request-service/.env.example apps/request-service/.env
cp apps/event-service/.env.example apps/event-service/.env
cp apps/api-gateway/.env.example apps/api-gateway/.env
```

Registration, login, and attendance require `MONGO_URI`. Login and attendance require `JWT_SECRET`. Request and event services require `MONGODB_URI`, `MONGODB_DB_NAME`, `JWT_SECRET`, and `JWT_ALGORITHM`. Gateway requires all five service URLs and same `JWT_SECRET` used by login and protected services.

Event image URLs should use gateway prefix:

```dotenv
PUBLIC_BASE_URL=http://localhost/event
UPLOAD_DIR=uploads
MAX_IMAGE_MB=5
MAX_IMAGES_PER_EVENT=10
```

Do not commit `.env` files or credentials. URL-encode reserved characters in MongoDB passwords.

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

## API contract

Gateway health, registration, and login are public. Every `/request/*`, `/event/*`, and `/attendance/*` gateway request requires `Authorization: Bearer <token>`. Use `http://localhost` through Nginx. Direct service exposure bypasses gateway authentication, but protected service handlers still enforce their own JWT dependencies.

### Gateway routes

| Method | Gateway path | Access | Destination |
| --- | --- | --- | --- |
| GET | `/health` | Public | Gateway |
| Any | `/register/*` | Public | Registration; prefix stripped |
| Any | `/auth/*` | Public | Login; prefix stripped |
| Any | `/request/*` | JWT required | Request; prefix stripped |
| Any | `/event/*` | JWT required | Event; prefix stripped |
| Any | `/attendance/*` | JWT required | Attendance; prefix stripped |

### Registration and login

| Method | Gateway path | Direct path | Access |
| --- | --- | --- | --- |
| POST | `/register/register` | `http://localhost:5001/register` | Public |
| POST | `/auth/login` | `http://localhost:5002/login` | Public |

Registration requires `name`, `emailid`, `pass`, and `mobile`; `role` defaults to `user`. Login requires `emailid`, `pass`, and `role`, and returns JWT valid for one hour.

### Request service

Gateway base: `/request/api/v1`

Direct base: `http://localhost:8000/api/v1`

| Method | Relative path | Access and behavior |
| --- | --- | --- |
| GET | `/health` | Direct route public; gateway route JWT-protected |
| POST | `/leave-requests` | JWT; create request |
| GET | `/leave-requests` | JWT; list current user's requests |
| GET | `/leave-requests/{request_id}` | JWT; owned record only |
| PATCH | `/leave-requests/{request_id}` | JWT; pending record only |
| PATCH | `/leave-requests/{request_id}/cancel` | JWT; pending record only |
| POST | `/pre-scholarship-registrations` | JWT; create registration |
| GET | `/pre-scholarship-registrations` | JWT; list current user's registrations |

Pre-scholarship get-one, update, and cancel handlers are disabled in source and are not API routes.

### Event service

Gateway base: `/event/api/v1`

Direct base: `http://localhost:8001/api/v1`

| Method | Relative path | Access and behavior |
| --- | --- | --- |
| POST | `/events` | Admin; create event |
| GET | `/events` | Authenticated; non-admin users receive published events |
| GET | `/events/{event_id}` | Authenticated; non-admin users can view published events |
| PATCH | `/events/{event_id}` | Admin; update event |
| DELETE | `/events/{event_id}` | Admin; delete event and referenced images |

Image upload and removal handlers are disabled. Existing uploaded files remain available directly under `/uploads/*`; gateway access through `/event/uploads/*` requires JWT.

### Attendance service

Gateway base: `/attendance`

Direct base: `http://localhost:8002`

| Method | Relative path | Access and behavior |
| --- | --- | --- |
| GET | `/health` | Direct public; gateway route JWT-protected |
| POST | `/check-in` | JWT; create current user's daily attendance |
| POST | `/check-out` | JWT; close current user's daily attendance |
| GET | `/me` | JWT; list current user's records |
| GET | `/` | Admin; list records with optional filters |
| PATCH | `/{id}` | Admin; update attendance record |

## Local development

Create service-specific `.env` files first. Run each command from repository root in separate terminal.

```bash
cd apps/api-gateway && npm ci && node index.js
cd apps/registration-service && npm ci && node index.js
cd apps/login-service && npm ci && node index.js
cd apps/attendance-service && npm ci && node server.js
cd apps/request-service && uv sync && uv run uvicorn app.main:app --reload --port 8000
cd apps/event-service && uv sync && uv run uvicorn app.main:app --reload --port 8001
```

For local processes, gateway service URLs must use `http://localhost:<port>` instead of Compose hostnames.

Direct endpoints:

- Gateway health: `http://localhost:4000/health`
- Request health: `http://localhost:8000/api/v1/health`
- Request OpenAPI: `http://localhost:8000/api/v1/openapi.json`
- Event OpenAPI: `http://localhost:8001/openapi.json`
- Attendance health: `http://localhost:8002/health`

## Repository layout

```text
apps/
  api-gateway/          Express gateway and JWT middleware
  registration-service/ Express registration API
  login-service/        Express login API and JWT issuance
  request-service/      FastAPI request APIs
  event-service/        FastAPI event API and uploads
  attendance-service/   Express attendance API
deploy/                 Empty EC2 deployment placeholders
nginx/                  Nginx load balancer configuration
docker-compose.yaml     Local orchestration configuration
AGENTS.md               Agent and contribution instructions
README.md               Project documentation
```

## Troubleshooting

### `Application startup failed`

```bash
docker compose logs --tail=200 request-service event-service
```

Confirm MongoDB URI, credentials, database name, network access, and DNS connectivity.

### `Bad Gateway`

```bash
docker compose ps
docker compose logs --tail=200 api-gateway
```

Confirm target service and gateway service URL.

### `401 Access Denied`

Use token returned by `/auth/login` in exact `Authorization: Bearer <token>` header. All token-verifying services must share `JWT_SECRET`.
