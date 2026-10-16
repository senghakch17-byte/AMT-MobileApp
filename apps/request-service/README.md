# Request Service

FastAPI service for leave requests and pre-scholarship registrations. Uses Beanie with external MongoDB.

## Structure

```text
app/
  api/
    deps.py
    health.py
    leave_requests.py
    pre_scholarship.py
    router.py
  core/
    config.py
    security.py
  database/
    models.py
    mongodb.py
    session.py
  schemas/
  utils/
  main.py
```

## Setup

Requires Python 3.12, `uv`, reachable MongoDB, and JWT secret shared with login and gateway services.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Required configuration includes `MONGODB_URI`, `MONGODB_DB_NAME`, `JWT_SECRET`, and `JWT_ALGORITHM`. Application startup pings MongoDB and fails when database is unreachable.

## URLs

- Direct base: `http://localhost:8000/api/v1`
- Gateway base: `http://localhost:4000/request/api/v1`
- Direct health: `http://localhost:8000/api/v1/health`
- Direct OpenAPI: `http://localhost:8000/api/v1/openapi.json`

Current app `root_path` is `/fastapi`, which does not match gateway prefix `/request`. Generated Swagger URLs may be incorrect until runtime configuration is reconciled.

All gateway `/request/*` traffic requires JWT. Direct health route has no service-level auth dependency; other active routes require JWT.

## Active routes

| Method | Relative path | Behavior |
| --- | --- | --- |
| GET | `/health` | Service health |
| POST | `/leave-requests` | Create leave request |
| GET | `/leave-requests` | List current user's requests |
| GET | `/leave-requests/{request_id}` | Get owned request |
| PATCH | `/leave-requests/{request_id}` | Update pending request |
| PATCH | `/leave-requests/{request_id}/cancel` | Cancel pending request |
| POST | `/pre-scholarship-registrations` | Create registration |
| GET | `/pre-scholarship-registrations` | List current user's registrations |

Pre-scholarship get-one, update, and cancel handlers are disabled in source and are not available routes.
