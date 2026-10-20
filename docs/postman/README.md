# OMS API testing in Postman

## Import and configure

1. Start the backend with `docker compose up --build`. The gateway should be reachable at `http://localhost`; MongoDB must be configured and reachable by the services.
2. In Postman, import `OMS-Backend.postman_collection.json` and `OMS-local.postman_environment.json` (Import → Files). Select **OMS local gateway** in the environment selector.
3. Set `userEmail` and `userPassword` to credentials for test account. **Register user** always sends role `user`; use fresh test email to expect `201`, or existing email to expect duplicate-account `400`. Keep `gatewayUrl` as is for local Docker, or change it to your deployed gateway URL.
4. `runPreScholarshipRegistration` and `runAttendanceMutation` default to `false`, so these setup or daily-state mutations skip during repeat runs. Set each to `true` only in controlled test data. Run **Login user (save userToken)**; it automatically stores JWT in selected environment. It expires after one hour; run login again after expiry.
5. Run folders in number order. Folder **01 - Load balancer and Gateway health** first: direct health checks verify `gateway1Url` and `gateway2Url`; four Nginx health requests collect `X-Upstream`, and final request fails unless two distinct Gateway upstreams served traffic. Collection auth sends `userToken` to protected endpoints. Admin requests explicitly use `adminToken`. **Members** uploads `docs/postman/fixtures/member-test-document.pdf`; select this file again if Postman cannot resolve path after import. **Library** creates booking history using separate time slots, then deletes only its disposable room and book.

## Admin token setup

An admin account is needed for event creation, update, and deletion. Public registration creates admin only for exact request role `admin`; all other or missing values create user. This allows public self-provisioning of administrators. Alternatively, set `ADMIN_NAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `ADMIN_MOBILE` in `apps/registration-service/.env`, then run `cd apps/registration-service && npm run provision-admin`. Set matching `adminEmail` and `adminPassword` in Postman, then run **Login admin (save adminToken)**. Event write requests read `adminToken`; user role tokens receive gateway `403`.

Both Request and Event services verify JWTs using the same `JWT_SECRET` as Login and the API Gateway. The gateway protects all `/request/*` and `/event/*` requests. Do not manually paste the token when using this collection; the login test script stores it, and collection/request auth sends it as `Authorization: Bearer <token>`.

## Endpoints and what to send

All URLs below are gateway URLs. `{{gatewayUrl}}` defaults to `http://localhost`.

| Method and path | Auth | Use / notes |
| --- | --- | --- |
| `GET /health` | None | Gateway liveness check. |
| `POST /register/register` | None | JSON: `name`, `emailid`, `pass`, `mobile`, optional `role`. Exact `role: "admin"` creates admin; all other or missing values create user. Returns 201. Duplicate email returns 400. |
| `POST /auth/login` | None | JSON: `emailid`, `pass`, and matching `role` (`user` or `admin`). Returns a one-hour JWT; collection stores the token. |
| `GET /request/health` | User token | Request service health. |
| `POST /request/leave-requests` | User token | JSON uses `leave_type` (`sick`, `personal`, etc. per API enum), ISO dates, reason of 10–500 chars, optional `attachment_urls`. Create returns an ID. Avoid overlapping active requests. |
| `GET /request/leave-requests` | User token | Lists only your requests. Optional `status`, `skip`, `limit` (1–100). |
| `GET /request/leave-requests/{{leaveRequestId}}` | User token | Fetch your request by ID; save an ID from create first. |
| `PATCH /request/leave-requests/{{leaveRequestId}}` | User token | Update a pending request only; send only fields to change. |
| `PATCH /request/leave-requests/{{leaveRequestId}}/cancel` | User token | Cancel a pending request. |
| `POST /request/pre-scholarship-registrations` | User token | Send required student/guardian/contact/school fields and `statement` (20–1500 chars). `academic_year` format `YYYY-YYYY`; `need_based` requires `monthly_family_income`; `merit` requires `academic_average`. |
| `GET /request/pre-scholarship-registrations` | User token | Lists your registrations; optional `status`, `skip`, `limit`. |
| `POST /event/events` | Admin token | Create an event. Use ISO datetimes; `status` defaults to `draft`. |
| `GET /event/events` | Any token | Lists events. Non-admins see published events only. Supports `category`, `upcoming`, `status` (admin filtering), `skip`, `limit`. |
| `GET /event/events/{{eventId}}` | Any token | Gets a published event for users; admins can see drafts. |
| `PATCH /event/events/{{eventId}}` | Admin token | Update supplied event fields; e.g. publish using `{"status":"published"}`. |
| `DELETE /event/events/{{eventId}}` | Admin token | Deletes event; successful response is 204. |
| `GET /attendance/health` | User token | Attendance service health through gateway. |
| `POST /attendance/check-in` | User token | Creates current user's daily attendance. Collection saves returned `_id` as `attendanceId`. |
| `POST /attendance/check-out` | User token | Closes current user's attendance for today. |
| `GET /attendance/me` | User token | Lists current user's records; supports optional `from` and `to` ISO dates. |
| `GET /attendance/` | Admin token | Lists records; supports optional `userID`, `from`, and `to` filters. |
| `PATCH /attendance/{{attendanceId}}` | Admin token | Updates `attendanceDate`, `checkIn`, `checkOut`, or `status`. |
| `GET /notification/health` | User token | Notification service health through gateway. |
| `GET /notification/api/v1/notifications` | User token | Lists accessible notifications. Optional `type`, `read`, `skip`, and `limit`. |
| `GET /notification/api/v1/notifications/unread-count` | User token | Returns unread count. |
| `GET /notification/api/v1/notifications/{{notificationId}}` | User token | Gets accessible notification; set `notificationId` from test data. |
| `PATCH /notification/api/v1/notifications/read-all` | User token | Marks all accessible unread notifications read. |
| `PATCH /notification/api/v1/notifications/{{notificationId}}/read` | User token | Marks notification read. |
| `DELETE /notification/api/v1/notifications/{{notificationId}}` | User token | Hides notification for current user. |
| `GET /notification/api/v1/notification-preferences/me` | User token | Gets current user's preferences. |
| `PATCH /notification/api/v1/notification-preferences/me` | User token | Updates `inAppEnabled` and/or supported `mutedTypes`. |
| `GET /members/health` | User token | Member service health through gateway. |
| `GET`, `PATCH /members/api/v1/members/me` | User token | Gets or updates own lazily-created profile. |
| `POST`, `GET /members/api/v1/members/me/documents` | User token | Uploads PDF/JPEG/PNG/WEBP document or lists own documents. After import, select `/Users/user/Documents/GitHub/AMT-MobileApp/docs/postman/fixtures/member-test-document.pdf` in `file` form-data field; Postman does not embed local file content in collection exports. A successful upload or non-empty list saves `memberDocumentId`. |
| `GET /members/api/v1/members/me/documents/{{memberDocumentId}}/download` | User token | Downloads own document. Request stops with clear error until `memberDocumentId` exists. |
| `GET /members/api/v1/members`, `/members/{{memberUserId}}`, and member document routes | Admin token | Lists members, gets profile, and accesses member document history/download. |
| `GET /library/health` | User token | Library service health through gateway. |
| `POST`, `GET /library/api/v1/rooms`; `GET /rooms/{{roomId}}`; `PATCH`, `DELETE /rooms/{{roomId}}`; `GET /rooms/{{roomId}}/availability` | User token; admin for writes | Room catalog and availability. |
| `POST /library/api/v1/bookings`; `GET /bookings/me`; `GET /bookings/{{bookingId}}`; `POST /bookings/{{bookingId}}/cancel` | User token | Creates, lists, gets, or cancels own booking. |
| `GET /library/api/v1/bookings`; `POST /bookings/{{bookingId}}/approve`; `POST /bookings/{{bookingId}}/reject` | Admin token | Booking history and decisions. |
| `POST`, `GET /library/api/v1/books`; `GET /books/{{bookId}}`; `PATCH`, `DELETE /books/{{bookId}}` | User token; admin for writes | Book catalog. |

## Load balancer and scope

`gatewayUrl` defaults to `http://localhost`, Nginx public entry point on port 80. Folder 01 tests this path and requires at least two distinct `X-Upstream` response header values, proving Nginx forwarded requests to both Gateway replicas. `gateway1Url` (`http://localhost:4000`) and `gateway2Url` (`http://localhost:4001`) are direct health checks only; do not use them for API workflow requests. Collection covers every public gateway endpoint, including Member and Library routes. Internal `POST /notification/api/v1/internal/events` is excluded because it is service-to-service only.

## Running requests in order

1. Run **01 - Load balancer and Gateway health** in request order. Final request requires two distinct `X-Upstream` values.
2. Register user → Login user.
3. Create leave request → its test script saves `leaveRequestId`; use Get, Update, or Cancel while it is pending. A cancelled request cannot be changed.
4. Set `runPreScholarshipRegistration=true` only when creating a new registration, then list registrations. An active duplicate for same academic year returns 409.
5. Provision/login admin in controlled environment → Create event → update event to `published` → list/get as user → delete as admin. Create saves returned `id` into `eventId` automatically.
6. Set `runAttendanceMutation=true` only when checking in/out for current UTC day. Collection saves `attendanceId` on check-in; list personal attendance always runs. Use admin token for list-all and update.
7. List notifications saves first returned `id` as `notificationId`. Item requests skip when no accessible notification exists. Preferences work without notification data. `POST /notification/api/v1/internal/events` is intentionally excluded: internal service-to-service route requires `x-internal-api-key` and must not be exposed through gateway.
8. Members: get profile to save `memberUserId`. In **Upload my document**, select `/Users/user/Documents/GitHub/AMT-MobileApp/docs/postman/fixtures/member-test-document.pdf` for `file` after import, then upload/list/download. Upload or non-empty list saves `memberDocumentId`. Run admin member document list before its download; it saves both IDs. Upload leaves test document history in database.
9. Library: create rooms, run pending/approved/rejected/cancelled booking flow, then create/update/delete catalog book. Booking room remains because booking history prevents room deletion.
10. Optional filters: add `?status=pending`, `?skip=0&limit=20`, `?category=announcement`, or `?upcoming=true` as applicable. Enum values are defined by API schemas.

## Common responses

- `401`: token missing, invalid, or expired. Login again; verify the Login service, API Gateway, Request, and Event services share `JWT_SECRET`.
- `403`: role mismatch at login or admin-only event or attendance route called using a user token.
- `404`: unknown ID or resource not owned by the current user; regular users cannot view draft events.
- `409`: overlapping active leave dates or duplicate active scholarship year.
- `422`: invalid body, date, enum, or query value.
- `502`: gateway cannot reach the upstream service; check `docker compose ps` and logs.

The direct service health/doc URLs are documented in the root README. These Postman requests use the gateway paths so they exercise gateway JWT authentication too.
