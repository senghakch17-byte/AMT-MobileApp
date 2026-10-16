# Event Service

FastAPI service for event management and event image storage. Uses Beanie with external MongoDB.

## Structure

```text
app/
  api/
    deps.py
    events.py
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
uv run uvicorn app.main:app --reload --port 8001
```

Required configuration includes `MONGODB_URI`, `MONGODB_DB_NAME`, `JWT_SECRET`, and `JWT_ALGORITHM`. Storage settings include `PUBLIC_BASE_URL`, `UPLOAD_DIR`, `MAX_IMAGE_MB`, and `MAX_IMAGES_PER_EVENT`. Application startup pings MongoDB and fails when database is unreachable.

## URLs

- Direct API base: `http://localhost:8001/api/v1`
- Gateway API base: `http://localhost:4000/event/api/v1`
- Direct uploads: `http://localhost:8001/uploads`
- Gateway uploads: `http://localhost:4000/event/uploads`
- Direct OpenAPI: `http://localhost:8001/openapi.json`

Current app `root_path` is `/events`, which does not match gateway prefix `/event`. Generated Swagger URLs may be incorrect until runtime configuration is reconciled.

All gateway `/event/*` traffic requires JWT. Event handlers also enforce authenticated-user or admin access.

## Active routes

| Method | Relative path | Access and behavior |
| --- | --- | --- |
| POST | `/events` | Admin; create event |
| GET | `/events` | Authenticated; non-admin users receive published events |
| GET | `/events/{event_id}` | Authenticated; non-admin users can view published events |
| PATCH | `/events/{event_id}` | Admin; update event |
| DELETE | `/events/{event_id}` | Admin; delete event and referenced images |
| GET | `/uploads/*` | Static files; gateway access requires JWT |

Image upload and removal handlers are disabled in source and are not available routes. Existing uploaded files remain served by static mount.
