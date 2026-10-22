# AGENTS.md

## Project Overview

AMT-MobileApp is a Docker Compose microservices backend for a mobile app.

- API style: REST
- Public entry: `nginx` load balancer on port `80`, routing to gateway replicas on container port `4000`; host debug ports are `4000` and `4001`
- Gateway: Node.js / Express in `apps/api-gateway`
- Node services: registration, login, attendance, and notification
- Python services: request, event, member, and library APIs using FastAPI
- Database: external MongoDB
- Deployment: local Docker Compose; EC2 Compose files exist but remain incomplete and unverified for production

## Service Map

- `apps/api-gateway/` — Express gateway, dynamic service proxy routing, and JWT middleware in `server.js` and `app.js`.
- `apps/registration-service/` — Express/Mongoose registration service.
- `apps/login-service/` — Express/Mongoose login service and JWT issuing.
- `apps/attendance-service/` — Express/Mongoose attendance check-in, check-out, and administration API.
- `apps/notification-service/` — Express/Mongoose in-app notifications, receipt state, preferences, and Redis event consumer.
- `apps/request-service/` — FastAPI/Beanie request APIs.
- `apps/event-service/` — FastAPI/Beanie event APIs and uploads.
- `apps/member-service/` — FastAPI/Beanie member profiles and document history APIs.
- `apps/library-service/` — FastAPI/Beanie room booking and book catalog APIs.
- `nginx/` — public load balancer configuration connected to root Compose.
- `deploy/` — EC2 compose placeholders. Do not claim production deployment is complete from these files alone.

## Architecture Rules

- Keep gateway routing in `apps/api-gateway/routes/proxyRoutes.js`, service targets in `apps/api-gateway/config/services.config.js`, and auth/error middleware in `apps/api-gateway/middleware/`.
- Keep attendance-service HTTP wiring in `routes/`, handlers in `controllers/`, JWT/error handling in `middleware/`, Mongoose schemas in `models/`, database setup in `config/`, and focused shared helpers in `utils/`. Keep `app.js` separate from `server.js` for testing.
- Attendance records use `userID`, never `studentId` or `userId`.
- Keep FastAPI routers in `app/api/`, schemas in `app/schemas/`, and database models in `app/database/models.py`.
- Keep service boundaries intact. Do not move business logic between services without approval.

## Coding Guidelines

- Make the smallest safe change.
- Prefer deletion over addition when behavior stays correct.
- Use standard library, platform features, or existing dependencies before adding code.
- Do not add packages unless necessary.
- Follow existing naming and file organization.
- Use async/await for asynchronous Node.js code.
- Use CommonJS in Node.js services unless the service already uses ESM.
- Use Python 3.12, FastAPI, Pydantic v2, and existing Beanie patterns in Python services.
- Keep functions small and focused.
- Avoid speculative abstractions, factories, or config for values that do not vary.

## API Contracts

- Preserve public gateway prefixes unless explicitly asked to break them:
	- `/register`
	- `/auth`
	- `/request`
	- `/event`
	- `/attendance`
	- `/notification`
	- `/members`
	- `/library`
	- `/health`
- Follow REST conventions and use appropriate HTTP status codes.
- Keep response shapes stable for mobile clients.
- Validate incoming requests at trust boundaries.
- Handle errors consistently with existing service patterns.
- Do not change database schemas or API contracts without approval.

## Documentation Sync

- When changing routes, ports, environment variables, service names, Compose paths, startup commands, proxy prefixes, authentication requirements, behavior, architecture, or deployment decisions, update affected documentation in the same change.
- When adding, removing, renaming, or materially changing a service, update `AGENTS.md` in the same change. Keep project overview, service map, architecture rules, API prefixes, environment variables, deployment status, and verification commands aligned with active code and configuration.
- Check `README.md`, service READMEs, `.env.example` files, Docker/Compose configuration, route tables, and `AGENTS.md`; update only files affected by the change.
- Document only behavior present in active code and configuration. Label disabled code, empty deployment files, and planned infrastructure explicitly as incomplete; do not present them as operational.
- Verify documented paths and commands from the repository root and distinguish direct-service URLs from gateway URLs.
- Keep public entry points, service ports, URL prefixes, required authentication, and environment variable names consistent across documentation and configuration.
- When changing active API routes, methods, request bodies, authentication, environment variables, or response-driven collection scripts, update both Postman YAML sources under `docs/postman/postman/` and exported JSON files `docs/postman/OMS-Backend.postman_collection.json` and `docs/postman/OMS-local.postman_environment.json` in the same change. Verify strict JSON parsing and JSON/YAML endpoint parity.
- Record changed architectural or operational decisions in the relevant existing document. Create a dedicated decision record only when explicitly requested or when no existing document can hold the decision clearly.
- Keep `docs/AWS_DEVELOPMENT.md` synchronized with EC2 topology, Compose paths, exposed ports, security-group requirements, deployment commands, and known deployment limitations.

## Security

- Never hardcode passwords, tokens, API keys, MongoDB URIs, or JWT secrets.
- Never commit `.env` files.
- Use environment variables for secrets and service URLs.
- Do not modify authentication, authorization, JWT, or password hashing logic without explicit approval.
- Enforce authorization on protected routes.
- Validate and sanitize user input.
- Be careful with `app.set('trust proxy', ...)`; only trust known proxy paths in deployments.

## Environment And Config

- MongoDB is external. Docker Compose does not provision MongoDB.
- Missing `.env` files may cause runtime failures even when Compose starts.
- Gateway service targets come from environment variables such as `REGISTER_SERVICE_URL`, `LOGIN_SERVICE_URL`, `REQUEST_SERVICE_URL`, `EVENT_SERVICE_URL`, `ATTENDANCE_SERVICE_URL`, and `NOTIFICATION_SERVICE_URL`.

## Testing And Verification

- Read relevant files before editing.
- Run the smallest meaningful verification for the changed area.
- Do not claim tests passed unless the command was executed.
- Current Node package `npm test` scripts may be placeholders. If so, report that no real test exists.
- Every active service must have tests covering its public routes, authentication and authorization rules, request validation, success paths, expected error paths, and persistence or external-boundary behavior. Update affected tests in same change whenever service behavior changes.
- Unit tests may stub external systems. Keep at least one documented integration check for database, proxy, or other real boundaries that stubs cannot prove.
- Useful checks:
	- `docker compose config`
	- `docker compose logs -f api-gateway`
	- `docker compose logs -f request-service event-service`
	- `cd apps/request-service && uv run uvicorn app.main:app --reload --port 8000`
	- `cd apps/event-service && uv run uvicorn app.main:app --reload --port 8001`
	- `cd apps/attendance-service && npm test`
	- `cd apps/notification-service && npm test`

## New Service Discovery

- Before designing or creating a new service, ask user to choose supported stack, such as Node.js/Express or Python/FastAPI. Do not choose stack without confirmation.
- Gather requirements needed to define service purpose and boundaries, users and roles, endpoints and contracts, validation and errors, data and persistence, authentication and authorization, events and integrations, gateway prefix and port, environment variables, background work or uploads, tests, and deployment placement.
- Inspect existing service conventions before proposing architecture.
- Suggest relevant useful features, security controls, edge cases, and simpler alternatives. Separate required scope from optional ideas and explain tradeoffs.
- Confirm unresolved API contract, schema, security, and service-boundary decisions before implementation. Existing conventions may answer minor details.
- After implementation, update tests, API contract, configuration examples, Compose files, README, AWS documentation when deployment changes, and `AGENTS.md`.

## Agent Workflow

1. Read relevant files before modifying code.
2. Explain major architectural changes before implementing them.
3. Make minimal changes necessary to complete the task.
4. Do not modify unrelated files.
5. Do not delete existing functionality without permission.
6. Reuse existing components and utilities.
7. Update affected documentation and examples in the same change.
8. Run relevant checks after changes when available.
9. Summarize changed files and verification results.

## Restrictions

- Do not rewrite whole services unnecessarily.
- Do not change database schemas without approval.
- Do not modify authentication or authorization logic without approval.
- Do not add dependencies unless necessary.
- Do not claim EC2 deployment readiness from placeholder files.