# AMT Mobile App Backend

A containerized backend starter for the AMT mobile app. It combines an Express API gateway, separate registration and login services, and a FastAPI service.

## Architecture

| Service | Container port | Host port | Purpose |
| --- | ---: | ---: | --- |
| API gateway | 4000 | 4000 | Routes client requests to backend services |
| Registration | 5001 | 5001 | Creates accounts and hashes passwords |
| Login | 5002 | 5002 | Checks credentials and issues JWTs |
| FastAPI | 8000 | 8000 | Python API with versioned health endpoint |

The gateway routes `/register/*` to registration, `/auth/*` to login, and `/fastapi/*` to FastAPI. The FastAPI app also serves its own health check at `/api/v1/health` and interactive API docs at `/docs` when accessed directly.

## Prerequisites

- Docker with Docker Compose
- A MongoDB instance reachable by both the registration and login services

MongoDB is not included in `docker-compose.yaml`; provide a MongoDB connection URI in both Node service environment files.

## Configuration

Create these files before starting Compose:

- `registration-service/.env`
- `login-service/.env`
- `api-gateway/.env`

Set the following values:

```dotenv
# registration-service/.env and login-service/.env
MONGO_URI=mongodb://<host>:27017/<database>
JWT_SECRET=<same-long-random-secret-in-both-services>
```

```dotenv
# api-gateway/.env
JWT_SECRET=<same-long-random-secret-in-both-services>
```

The gateway currently forwards requests to FastAPI without enabling its JWT authentication middleware. `JWT_SECRET` is read by the gateway, but the protected gateway middleware is not currently attached to a route. Keep secrets out of source control and use the same JWT secret for token signing and verification if you enable that middleware.

## Run with Docker Compose

From the repository root:

```bash
docker compose up --build
```

To stop the services:

```bash
docker compose down
```

Compose publishes the gateway and service ports on the host. The gateway waits for its three upstream containers to start, but Compose startup ordering does not guarantee that MongoDB is ready or available.

## API endpoints

### Register an account

`POST http://localhost:4000/register/userregister`

```json
{
  "name": "Example User",
  "emailid": "user@example.com",
  "pass": "your-password",
  "mobile": "5550100",
  "role": "user"
}
```

The `role` field is optional and defaults to `user`. The service hashes the password before saving the account. A successful request returns `201`.

### Log in

`POST http://localhost:4000/auth/login`

```json
{
  "emailid": "user@example.com",
  "pass": "your-password",
  "role": "user"
}
```

A successful response includes a JWT that expires after one hour.

### Gateway health

`GET http://localhost:4000/health`

### FastAPI health and docs

- Through the gateway: `GET http://localhost:4000/fastapi/api/v1/health`
- Directly: `GET http://localhost:8000/api/v1/health`
- Swagger UI: `http://localhost:8000/docs`

The FastAPI health response includes the configured environment. Its database connection code is currently a placeholder and skips initialization when `DATABASE_URL` is unset.

## Local development

Run individual services outside Docker after installing their dependencies. The Node services use `npm install` (or `npm ci`); the FastAPI service uses `uv`:

```bash
cd fastapi_environment
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

The Node services load their `.env` files from their own directories. The gateway expects its upstream URLs to be configured as `REGISTER_SERVICE_URL`, `LOGIN_SERVICE_URL`, and `FASTAPI_SERVICE_URL`; Compose sets these to the internal service addresses automatically.

## Repository layout

```text
api-gateway/          Express gateway and reverse proxy
registration-service/ Express registration API and MongoDB model
login-service/        Express login API, MongoDB model, and JWT issuance
fastapi_environment/  FastAPI application and Python dependencies
docker-compose.yaml   Local multi-container orchestration
```
