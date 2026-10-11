# Application Architecture (`app/`)

This directory contains the core source code for the FastAPI backend service.

## Directory Structure Overview

* **`api/`**: API route definitions and versioning.
    * **`endpoints/`**: Individual endpoint route handlers (e.g., `health.py`, `users.py`).
    * **`router.py`**: Central router aggregating all v1 endpoint sub-routers.
* **`core/`**: Application configuration and global setup.
  * `config.py`: Environment variable loading and validation via `pydantic-settings`.
* **`database/`**: Database connection lifecycles and session management.
  * Ready to configure drivers for either PostgreSQL (`asyncpg` + `sqlalchemy` / `sqlmodel`) or MongoDB (`motor` / `beanie`).
* **`schemas/`**: Pydantic models for request validation and response serialization.
* **`utils/`**: Helper utilities, custom loggers, and shared helper functions.
* **`main.py`**: Application factory, lifespan context manager, and entry point.

---

## Development Setup with `uv`

### Prerequisites
Install `uv` package manager:
```bash
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh


uv sync
uv run uvicorn app.main:app --reload --port 8000
Swagger UI: http://localhost:8000/docs