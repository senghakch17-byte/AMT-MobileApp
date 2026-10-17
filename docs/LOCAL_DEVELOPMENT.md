# Local Development

Create service-specific `.env` files first. Run each command from repository root in separate terminal.

```bash
cd apps/api-gateway && npm ci && node server.js
cd apps/registration-service && npm ci && node index.js
cd apps/login-service && npm ci && node index.js
cd apps/attendance-service && npm ci && node server.js
cd apps/request-service && uv sync && uv run uvicorn app.main:app --reload --port 8000
cd apps/event-service && uv sync && uv run uvicorn app.main:app --reload --port 8001
```

Run service tests:

```bash
./test-all.sh

# Or run one service suite:
cd apps/api-gateway && npm test
cd apps/registration-service && npm test
cd apps/login-service && npm test
cd apps/attendance-service && npm test
cd apps/notification-service && npm test
cd apps/request-service && uv sync && uv run pytest
cd apps/event-service && uv sync && uv run pytest
cd apps/member-service && uv sync && uv run pytest
cd apps/library-service && uv sync && uv run pytest
```

For local processes, gateway service URLs must use `http://localhost:<port>` instead of Compose hostnames.

Direct endpoints:

- Gateway health: `http://localhost:4000/health`
- Request health: `http://localhost:8000/health`
- Request OpenAPI: `http://localhost:8000/openapi.json`
- Event OpenAPI: `http://localhost:8001/openapi.json`
- Attendance health: `http://localhost:8002/health`
