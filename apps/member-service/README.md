# Member Service

FastAPI + MongoDB (Beanie) service for **member profiles** and **document history**.
Same layout and conventions as `event-service`: JWT bearer tokens issued elsewhere
(`id`, `emailid`, `role` claims), routed through the gateway under `/members`.

## Endpoints (`/api/v1`)

| Method | Path | Who | What |
|---|---|---|---|
| GET | `/members/me` | any user | View own profile (created on first call) |
| PATCH | `/members/me` | any user | Edit own profile (`full_name`, `phone`, `address`, `date_of_birth`) |
| POST | `/members/me/documents` | any user | Upload a document (multipart: `file`, `title`, `doc_type`, `description`, `document_date`) |
| GET | `/members/me/documents` | any user | Own document history, newest first (`doc_type`, `skip`, `limit`) |
| GET | `/members/me/documents/{id}/download` | any user | Download own document |
| GET | `/members` | **admin** | View all users (`q` name/email search, `role`, `skip`, `limit`) |
| GET | `/members/{user_id}` | admin, or that user | View a profile |
| GET | `/members/{user_id}/documents` | admin, or that user | View a member's document history |
| GET | `/members/{user_id}/documents/{id}/download` | admin, or that user | Download a member's document |
| GET | `/health` | public | Health check |

List endpoints return the total in an `X-Total-Count` header.
`user_id` is the auth service's user id (the JWT `id` claim), not the Mongo `_id`.

## Design notes

- **Profiles are created lazily.** This service has no sign-up; a profile is created from the
  token the first time a user calls `/members/me`, and its email/role are refreshed from the
  token on later calls. So **admin "view all users" lists users who have used this service**,
  not every account in the auth service.
- **Documents are private.** Unlike event images, files are *not* mounted as static files.
  They are downloaded through authenticated endpoints that check ownership. Type is detected
  from the file's bytes (PDF, JPEG, PNG, WEBP), not the filename or `Content-Type` header.
- Document history is append-only: there is no edit or delete endpoint.

## Development setup with `uv`

```bash
uv sync
cp .env.example .env        # set MONGODB_URI and the same JWT_SECRET as the auth service
uv run uvicorn app.main:app --reload --port 8002
```

Swagger UI: http://localhost:8002/docs

## Tests

```bash
uv run pytest                                        # auth/validation tests; DB tests skip
MONGODB_TEST_URI=mongodb://localhost:27017 uv run pytest   # also runs the end-to-end DB tests
```

DB tests use a throwaway database named `member_service_test`.

## Docker

```bash
docker build -t member-service .
docker run -p 8002:8002 --env-file .env member-service
```

Mount a volume at `/backend/uploads` so uploaded documents survive container restarts.
