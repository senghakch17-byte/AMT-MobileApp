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

- Direct API base: `http://localhost:8001`
- Gateway API base: `http://localhost/announcement`
- Direct uploads: `http://localhost:8001/uploads`
- Gateway uploads: `http://localhost/announcement/uploads`
- Direct OpenAPI: `http://localhost:8001/openapi.json`

Gateway proxy strips `/announcement` before forwarding to direct-service routes.

All gateway `/announcement/*` traffic requires JWT. Event handlers also enforce authenticated-user or admin access.

## Active routes

| Method | Relative path | Access and behavior |
| --- | --- | --- |
| POST | `/announcements` | Admin; create event |
| GET | `/announcements` | Authenticated; non-admin users receive published events |
| GET | `/announcements/{event_id}` | Authenticated; non-admin users can view published events |
| PATCH | `/announcements/{event_id}` | Admin; update event |
| DELETE | `/announcements/{event_id}` | Admin; delete event and referenced images |
| GET | `/uploads/*` | Static files; gateway access requires JWT |

Image upload and removal handlers are disabled in source and are not available routes. Existing uploaded files remain served by static mount.

## Tests

```bash
uv sync
uv run pytest
```

Route and schema tests run without MongoDB. Add `MONGODB_TEST_URI` when integration tests are added.
