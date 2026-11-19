# OMS API testing in Postman

## Import and configure

1. Start the backend with `docker compose up --build`. The gateway should be reachable at `http://localhost`; MongoDB must be configured and reachable by the services.
2. In Postman, import `OMS-Backend.postman_collection.json` and `OMS-local.postman_environment.json` (Import → Files). Select **OMS local gateway** in the environment selector.
3. Set `userPassword` plus admin credentials. **Register user** creates unique `postman-<timestamp>@example.com` value each run, then **Login user** uses it. Do not set `userEmail` manually when running full collection. Keep `gatewayUrl` for local Docker, or set it to deployed Nginx URL such as `http://EC2_A_PUBLIC_IP`.
4. Every collection request sends; no mutation request skips. Run **Login user (save userToken)** after registration. It stores JWT in selected environment and expires after one hour. Admin requests require working `adminEmail` and `adminPassword`.
5. Run folders in number order. Folder **01 - Load balancer and Gateway health** first. For Minikube, set `gatewayUrl` to `http://oms.aupp.local` and use its Nginx health requests only; compare `X-Gateway-Instance` values to prove both gateway replicas serve traffic. Collection auth sends `userToken` to protected endpoints. Admin requests explicitly use `adminToken`. **Users** uploads `docs/postman/fixtures/user-test-document.pdf`; select this file again if Postman cannot resolve its path after import. **Booking** creates booking history using separate time slots, then deactivates only its disposable room.

## Admin token setup

An admin account is needed for announcement creation, update, and deletion. Public registration always creates a `user` account and ignores a supplied role. Create an admin in a controlled environment by setting `ADMIN_NAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `ADMIN_MOBILE` in `apps/registration-service/.env`, then run `cd apps/registration-service && npm run provision-admin`. Set matching `adminEmail` and `adminPassword` in Postman, then run **Login admin (save adminToken)**. Announcement write requests read `adminToken`; user role tokens receive gateway `403`.

Both Request and Announcement services verify JWTs using the same `JWT_SECRET` as Login and the API Gateway. The gateway protects all `/request/*` and `/announcement/*` requests. Do not manually paste the token when using this collection; the login test script stores it, and collection/request auth sends it as `Authorization: Bearer <token>`.

## Endpoints and what to send

All URLs below are gateway URLs. `{{gatewayUrl}}` defaults to `http://localhost`.

| Method and path | Auth | Use / notes |
| --- | --- | --- |
| `GET /health` | None | Gateway liveness check. |
| `POST /register` | None | JSON: `name`, `emailid`, `pass`, `mobile`. Registration always creates a user. Returns 201. Duplicate email returns 400. |
| `POST /login` | None | JSON: `emailid`, `pass`, and matching `role` (`user` or `admin`). Returns a one-hour JWT; collection stores the token. |
| `GET /request/health` | User token | Request service health. |
| `POST /request/leave-requests` | User token | JSON uses `leave_type` (`sick`, `personal`, etc. per API enum), ISO dates, reason of 10–500 chars, optional `attachment_urls`. Create returns an ID. Avoid overlapping active requests. |
| `GET /request/leave-requests` | User token | Lists only your requests. Optional `status`, `skip`, `limit` (1–100). |
| `GET /request/leave-requests/{{leaveRequestId}}` | User token | Fetch your request by ID; save an ID from create first. |
| `PATCH /request/leave-requests/{{leaveRequestId}}` | User token | Update a pending request only; send only fields to change. |
| `PATCH /request/leave-requests/{{leaveRequestId}}/cancel` | User token | Cancel a pending request. |
| `POST /announcement` | Admin token | Create an announcement. Use ISO datetimes; `status` defaults to `draft`. |
| `GET /announcement` | Any token | Lists announcements. Non-admins see published announcements only. Supports `category`, `upcoming`, `status` (admin filtering), `skip`, `limit`. |
| `GET /announcement/{{announcementId}}` | Any token | Gets a published announcement for users; admins can see drafts. |
| `PATCH /announcement/{{announcementId}}` | Admin token | Update supplied announcement fields; e.g. publish using `{"status":"published"}`. |
| `DELETE /announcement/{{announcementId}}` | Admin token | Deletes announcement; successful response is 204. |
| `GET /attendance/health` | User token | Attendance service health through gateway. |
| `POST /attendance/check-in` | User token | Creates current user's daily attendance. Collection saves returned `_id` as `attendanceId`. |
| `POST /attendance/check-out` | User token | Closes current user's attendance for today. |
| `GET /attendance/me` | User token | Lists current user's records; supports optional `from` and `to` ISO dates. |
| `GET /attendance/` | Admin token | Lists records; supports optional `userID`, `from`, and `to` filters. |
| `PATCH /attendance/{{attendanceId}}` | Admin token | Updates `attendanceDate`, `checkIn`, `checkOut`, or `status`. |
| `GET /notification/health` | User token | Notification service health through gateway. |
| `GET /notification` | User token | Lists accessible notifications. Optional `type`, `read`, `skip`, and `limit`. |
| `GET /notification/unread-count` | User token | Returns unread count. |
| `GET /notification/{{notificationId}}` | User token | Gets accessible notification; set `notificationId` from test data. |
| `PATCH /notification/read-all` | User token | Marks all accessible unread notifications read. |
| `PATCH /notification/{{notificationId}}/read` | User token | Marks notification read. |
| `DELETE /notification/{{notificationId}}` | User token | Hides notification for current user. |
| `GET /notification/preferences/me` | User token | Gets current user's preferences. |
| `PATCH /notification/preferences/me` | User token | Updates `inAppEnabled` and/or supported `mutedTypes`. |
| `GET /user/health` | User token | User service health through gateway. |
| `GET`, `PATCH /user/me` | User token | Gets or updates own lazily-created profile. |
| `POST`, `GET /user/me/documents` | User token | Uploads PDF/JPEG/PNG/WEBP document or lists own documents. After import, select `/Users/user/Documents/GitHub/AMT-MobileApp/docs/postman/fixtures/user-test-document.pdf` in `file` form-data field; Postman does not embed local file content in collection exports. A successful upload or non-empty list saves `userDocumentId`. |
| `GET /user/me/documents/{{userDocumentId}}/download` | User token | Downloads own document. Request stops with clear error until `userDocumentId` exists. |
| `GET /user`, `/user/{{userUserId}}`, and user document routes | Admin token | Lists users, gets profile, and accesses user document history/download. |
| `GET /booking/health` | User token | Booking service health through gateway. |
| `POST`, `GET /booking/rooms`; `GET`, `PATCH`, `DELETE /booking/rooms/{{roomId}}`; `GET /booking/rooms/{{roomId}}/availability` | User token; admin for room writes | Room catalog and availability. |
| `POST /booking`; `GET /booking/me`; `GET /booking/{{bookingId}}`; `POST /booking/{{bookingId}}/cancel` | User token | Creates, lists, gets, or cancels own booking. |
| `GET /booking`; `POST /booking/{{bookingId}}/approve`; `POST /booking/{{bookingId}}/reject` | Admin token | Booking history and decisions. |

## Load balancer and scope

`gatewayUrl` defaults to `http://localhost`, Nginx's local public entry point. For the Minikube demonstration, set it to `http://oms.aupp.local`. Folder 01 requires two distinct `X-Gateway-Instance` response header values, proving Nginx forwarded requests to both gateway replicas. Direct gateway URLs are local troubleshooting checks only; do not use them for API workflows. Collection covers every public gateway endpoint. Internal `POST /internal/events` is excluded because it is service-to-service only.

## Running requests in order

1. Run **01 - Load balancer and Gateway health** in request order. Final request requires two distinct `X-Gateway-Instance` values.
2. Register user → Login user.
3. Create leave request → its test script saves `leaveRequestId`; use Get, Update, or Cancel while it is pending. A cancelled request cannot be changed.
4. Provision/login admin → create an announcement → publish it → verify the notification → list/get it as a user → delete it as admin. Verification searches matching `data.announcement_id`; Collection Runner retries while Redis processes the notification. Create saves the returned ID into `announcementId`.
5. Run **Check in** → **Check out** → **List my attendance** → admin update → **Verify attendance correction notification**. Check-in saves `_id` as `attendanceId`; checkout expects `200`. Admin correction proves matching `data.attendance_id`.
6. List notifications saves the first returned `id` as `notificationId`, then get, mark-read, and delete use it. Preferences work without notification data. `POST /internal/events` is intentionally excluded because it requires `x-internal-api-key` and is never routed through the gateway.
7. Users: get profile to save `userUserId`. In **Upload my document**, select `docs/postman/fixtures/user-test-document.pdf` for `file` after import, then upload/list/download. Upload or a non-empty list saves `userDocumentId`. Run admin user document list before its download; it saves both IDs.
8. Booking: create rooms, run pending/approved/rejected/cancelled booking flow, then deactivate the disposable room. Booking history remains available after room deactivation.
9. Optional filters: add `?status=pending`, `?skip=0&limit=20`, `?category=announcement`, or `?upcoming=true` as applicable. Enum values are defined by API schemas.

## Common responses

- `401`: token missing, invalid, or expired. Login again; verify the Login service, API Gateway, Request, and Announcement services share `JWT_SECRET`.
- `403`: role mismatch at login or admin-only announcement or attendance route called using a user token.
- `404`: unknown ID or resource not owned by the current user; regular users cannot view draft announcements.
- `409`: overlapping active leave dates or a second attendance check-in for the same user and UTC day. Run **List my attendance** to recover today’s `attendanceId` for admin correction.
- `422`: invalid body, date, enum, or query value.
- `502`: gateway cannot reach the upstream service; check `docker compose ps` and logs.

The direct service health/doc URLs are documented in the root README. These Postman requests use the gateway paths so they exercise gateway JWT authentication too.
