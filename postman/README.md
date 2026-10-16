sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss# AMT API testing in Postman

## Import and configure

1. Start the backend with `docker compose up --build`. The gateway should be reachable at `http://localhost:4000`; MongoDB must be configured and reachable by the services.
2. In Postman, import `AMT-Backend.postman_collection.json` and `AMT-local.postman_environment.json` (Import → Files). Select **AMT local gateway** in the environment selector.
3. Set `userEmail` and `userPassword` to a new account you can register. Keep `gatewayUrl` as is for local Docker, or change it to your deployed gateway URL.
4. Run **Register user**, then **Login user (save userToken)**. Login automatically stores the JWT in the selected environment. It expires after one hour; run login again after expiry.
5. Run the requests under **Leave requests** and **Events**. Collection auth sends `userToken` to protected endpoints. Event create/update/delete explicitly use `adminToken`.

## Admin token setup

An admin account is needed for event creation, update, and deletion. In a controlled local/test database only, set `adminEmail` and `adminPassword`, run **Register admin (only when authorized)** once, then **Login admin (save adminToken)**. The current registration service accepts `role: "admin"` from the public body, so do not expose this self-registration behavior in production. Use an administrator account created through your trusted provisioning process. The event write requests read `adminToken`; user role tokens receive 403.

Both Request and Event services verify JWTs using the same `JWT_SECRET` as Login and the API Gateway. The gateway protects all `/request/*` and `/event/*` requests. Do not manually paste the token when using this collection; the login test script stores it, and collection/request auth sends it as `Authorization: Bearer <token>`.

## Endpoints and what to send

All URLs below are gateway URLs. `{{gatewayUrl}}` defaults to `http://localhost:4000`.

| Method and path | Auth | Use / notes |
| --- | --- | --- |
| `GET /health` | None | Gateway liveness check. |
| `POST /register/register` | None | JSON: `name`, `emailid`, `pass`, `mobile`; optional `role` defaults to `user`. Returns 201. Duplicate email returns 400. |
| `POST /auth/login` | None | JSON: `emailid`, `pass`, and matching `role` (`user` or `admin`). Returns a one-hour JWT; collection stores the token. |
| `GET /request/api/v1/health` | User token | Request service health. |
| `POST /request/api/v1/leave-requests` | User token | JSON uses `leave_type` (`sick`, `personal`, etc. per API enum), ISO dates, reason of 10–500 chars, optional `attachment_urls`. Create returns an ID. Avoid overlapping active requests. |
| `GET /request/api/v1/leave-requests` | User token | Lists only your requests. Optional `status`, `skip`, `limit` (1–100). |
| `GET /request/api/v1/leave-requests/{{leaveRequestId}}` | User token | Fetch your request by ID; save an ID from create first. |
| `PATCH /request/api/v1/leave-requests/{{leaveRequestId}}` | User token | Update a pending request only; send only fields to change. |
| `PATCH /request/api/v1/leave-requests/{{leaveRequestId}}/cancel` | User token | Cancel a pending request. |
| `POST /request/api/v1/pre-scholarship-registrations` | User token | Send required student/guardian/contact/school fields and `statement` (20–1500 chars). `academic_year` format `YYYY-YYYY`; `need_based` requires `monthly_family_income`; `merit` requires `academic_average`. |
| `GET /request/api/v1/pre-scholarship-registrations` | User token | Lists your registrations; optional `status`, `skip`, `limit`. |
| `POST /event/api/v1/events` | Admin token | Create an event. Use ISO datetimes; `status` defaults to `draft`. |
| `GET /event/api/v1/events` | Any token | Lists events. Non-admins see published events only. Supports `category`, `upcoming`, `status` (admin filtering), `skip`, `limit`. |
| `GET /event/api/v1/events/{{eventId}}` | Any token | Gets a published event for users; admins can see drafts. |
| `PATCH /event/api/v1/events/{{eventId}}` | Admin token | Update supplied event fields; e.g. publish using `{"status":"published"}`. |
| `DELETE /event/api/v1/events/{{eventId}}` | Admin token | Deletes event; successful response is 204. |

## Running requests in order

1. Register user → Login user.
2. Create leave request → its test script saves `leaveRequestId`; use Get, Update, or Cancel while it is pending. A cancelled request cannot be changed.
3. Create pre-scholarship registration → List registrations. An active duplicate for the same academic year returns 409.
4. Register/login admin in a controlled environment → Create event. The create request saves its returned `id` into `eventId` automatically; then list/get/update/delete. Update the event to `published` to make it visible to a regular user.
5. Optional filters: add `?status=pending`, `?skip=0&limit=20`, `?category=announcement`, or `?upcoming=true` as applicable. Enum values are defined by the API schemas.

## Common responses

- `401`: token missing, invalid, or expired. Login again; verify the Login service, API Gateway, Request, and Event services share `JWT_SECRET`.
- `403`: role mismatch at login or admin-only event route called using a user token.
- `404`: unknown ID or resource not owned by the current user; regular users cannot view draft events.
- `409`: overlapping active leave dates or duplicate active scholarship year.
- `422`: invalid body, date, enum, or query value.
- `502`: gateway cannot reach the upstream service; check `docker compose ps` and logs.

The direct service health/doc URLs are documented in the root README. These Postman requests use the gateway paths so they exercise gateway JWT authentication too.

