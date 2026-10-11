# AMT Mobile App Backend

This repository contains the containerized backend for the AMT mobile application. It is a small microservice system with an Express API gateway, authentication services, and FastAPI services for leave requests, pre-scholarship registrations, and events.

## Architecture

```text
Mobile app
    |
    v
API gateway :4000
    |-- /register  -> Registration service :5001
    |-- /auth      -> Login service :5002
    |-- /request   -> Request service :8000
    `-- /event     -> Event service :8001

Registration service, Login service, Request service, and Event service
    `-------------------------> MongoDB

Event service ---> /backend/uploads
                       |
                       v
                 event_uploads volume
```

| Service | Container name | Host port | Responsibility |
| --- | --- | ---: | --- |
| API gateway | `api-gateway` | 4000 | Public entry point, routing, and JWT authentication |
| Registration service | `registration-service` | 5001 | Account creation and password hashing |
| Login service | `login-service` | 5002 | Credential validation and JWT issuance |
| Request service | `request-service` | 8000 | Leave requests and pre-scholarship registrations |
| Event service | `event-service` | 8001 | Event management and event image storage |

All services are connected to the Docker Compose `app-net` network. MongoDB is not provisioned by Compose; the registration and login services use `MONGO_URI`, while the request and event services use `MONGODB_URI`.

## Prerequisites

- Docker Desktop with Docker Compose
- A reachable MongoDB or MongoDB Atlas deployment
- A MongoDB user with access to the configured database
- A shared JWT secret for the login service, gateway, request service, and event service

The FastAPI services require Python 3.12 and `uv` only when running them outside Docker.

## Configuration

Copy each environment template and replace its values:

```powershell
Copy-Item registration-service\.env.example registration-service\.env
Copy-Item login-service\.env.example login-service\.env
Copy-Item request-service\.env.example request-service\.env
Copy-Item event-service\.env.example event-service\.env
Copy-Item api-gateway\.env.example api-gateway\.env
```

### Required settings

`registration-service/.env` and `login-service/.env`:

```dotenv
PORT=5001 # use 5002 in login-service
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/final_project
JWT_SECRET=<long-random-secret>
```

`request-service/.env` and `event-service/.env`:

```dotenv
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/final_project
MONGODB_DB_NAME=final_project
JWT_SECRET=<the-same-secret-used-by-login-service>
JWT_ALGORITHM=HS256
```

The event service also uses:

```dotenv
PUBLIC_BASE_URL=http://localhost:4000/events
UPLOAD_DIR=uploads
MAX_IMAGE_MB=5
MAX_IMAGES_PER_EVENT=10
```

The gateway needs the internal service URLs. `docker-compose.yaml` overrides these URLs for the Compose network:

```dotenv
PORT=4000
REGISTER_SERVICE_URL=http://registration-service:5001
LOGIN_SERVICE_URL=http://login-service:5002
REQUEST_SERVICE_URL=http://request-service:8000
EVENT_SERVICE_URL=http://event-service:8001
JWT_SECRET=<the-same-secret-used-by-login-service>
```

Do not commit `.env` files or real credentials. If a MongoDB password contains characters such as `@`, `:`, `/`, or `#`, URL-encode the password before putting it in the connection URI.

## Run with Docker Compose

From the repository root:

```powershell
docker compose up --build
```

Run in the background:

```powershell
docker compose up -d --build
```

View service logs:

```powershell
docker compose logs -f api-gateway
docker compose logs -f request-service event-service
```

Stop the stack:

```powershell
docker compose down
```

Stop the stack and remove the event upload volume:

```powershell
docker compose down -v
```

The gateway starts after the four upstream containers are started, but Compose does not wait for MongoDB to become reachable. The request and event services explicitly run a MongoDB `ping` during FastAPI startup. If MongoDB is unavailable, those services exit with `Application startup failed`; check the full `ServerSelectionTimeoutError` or authentication error in their logs.

## API routes

The gateway requires a bearer token for `/request/*` and `/event/*`. Registration and login are public.

### Registration and authentication

Register a user:

```http
POST http://localhost:4000/register/register
Content-Type: application/json
```

```json
{
  "name": "Example User",
  "emailid": "user@example.com",
  "pass": "your-password",
  "mobile": "5550100",
  "role": "user"
}
```

The `role` field defaults to `user`. A successful registration returns HTTP `201`.

Log in:

```http
POST http://localhost:4000/auth/login
Content-Type: application/json
```

```json
{
  "emailid": "user@example.com",
  "pass": "your-password",
  "role": "user"
}
```

The login response contains a JWT that expires after one hour. Send it to protected routes as:

```http
Authorization: Bearer <token>
```

### Request service

Direct service URLs use `http://localhost:8000`; gateway URLs use the `/request` prefix.

| Method | Gateway path | Description |
| --- | --- | --- |
| GET | `/request/api/v1/health` | Request service health |
| POST | `/request/api/v1/leave-requests` | Create a leave request |
| GET | `/request/api/v1/leave-requests` | List the current user's leave requests |
| GET | `/request/api/v1/leave-requests/{request_id}` | Get one leave request |
| PATCH | `/request/api/v1/leave-requests/{request_id}` | Update a pending leave request |
| PATCH | `/request/api/v1/leave-requests/{request_id}/cancel` | Cancel a pending leave request |
| POST | `/request/api/v1/pre-scholarship-registrations` | Create a pre-scholarship registration |
| GET | `/request/api/v1/pre-scholarship-registrations` | List the current user's registrations |

The same routes are available directly at `http://localhost:8000/api/v1/...` when bypassing the gateway.

### Event service

Direct service URLs use `http://localhost:8001`; gateway URLs use the `/event` prefix.

| Method | Gateway path | Access |
| --- | --- | --- |
| POST | `/event/api/v1/events` | Admin only; create an event |
| GET | `/event/api/v1/events` | Authenticated users; list published events |
| GET | `/event/api/v1/events/{event_id}` | Authenticated users; get an event |
| PATCH | `/event/api/v1/events/{event_id}` | Admin only; update an event |
| DELETE | `/event/api/v1/events/{event_id}` | Admin only; delete an event |

Event image upload and removal routes are present in the source as under-development code and are not currently enabled.

The event service exposes uploaded files from `/uploads`. Its persistent Docker volume is mounted at `/backend/uploads`.

### Health and API documentation

- Gateway health: `GET http://localhost:4000/health`
- Request service health: `GET http://localhost:8000/api/v1/health`
- Request service Swagger UI: `http://localhost:8000/docs`
- Request service OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`
- Event service Swagger UI: `http://localhost:8001/docs`
- Event service OpenAPI JSON: `http://localhost:8001/openapi.json`

The FastAPI applications use `/fastapi` and `/events` as their configured proxy root paths for generated URLs. Use the gateway paths shown above when calling them through the gateway.

## Local development without Docker

Create and populate the service-specific `.env` files first, then install dependencies in each service directory.

For an Express service:

```powershell
cd api-gateway
npm install
node index.js
```

Repeat the same pattern in `registration-service` and `login-service`. Use the service's configured port (`4000`, `5001`, or `5002`).

For the request service:

```powershell
cd request-service
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

For the event service:

```powershell
cd event-service
uv sync
uv run uvicorn app.main:app --reload --port 8001
```

When running services locally, set the gateway URLs to `http://localhost:<port>` rather than the Docker service hostnames.

## Repository layout

```text
api-gateway/          Express gateway, routing, and JWT middleware
registration-service/ Express registration API and MongoDB model
login-service/        Express login API, MongoDB model, and JWT issuance
request-service/      FastAPI leave-request and pre-scholarship APIs
event-service/        FastAPI event API and image storage
docker-compose.yaml   Local multi-container orchestration
postman/              API Gateway Postman collection and shared variables
```

## Troubleshooting

### `Application startup failed`

Inspect the request or event service logs:

```powershell
docker compose logs --tail=200 request-service event-service
```

Both FastAPI services ping MongoDB before startup completes. Confirm that the URI, credentials, database name, Atlas network access rules, and DNS/network connectivity are correct.

### `Bad Gateway`

Check that the target service is running and that the gateway has the correct internal URLs:

```powershell
docker compose ps
docker compose logs --tail=200 api-gateway
```

### `401 Access Denied`

Use the token returned by `/auth/login` and include the exact `Authorization: Bearer <token>` header. Ensure every service that verifies tokens uses the same `JWT_SECRET`.
