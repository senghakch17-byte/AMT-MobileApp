# API Contract

Gateway health, registration, and login are public. Every `/request/*`, `/event/*`, `/attendance/*`, `/notification/*`, `/members/*`, and `/library/*` gateway request requires `Authorization: Bearer <token>`. Gateway returns `403` before proxying documented admin-only Event, Attendance, and Library routes; services retain their own authorization checks. Use `http://localhost` through Nginx. Direct service exposure bypasses gateway authentication, but protected service handlers still enforce their own JWT dependencies.

### Gateway routes

| Method | Gateway path | Access | Destination |
| --- | --- | --- | --- |
| GET | `/health` | Public | Gateway |
| Any | `/register/*` | Public | Registration; prefix stripped |
| Any | `/auth/*` | Public | Login; prefix stripped |
| Any | `/request/*` | JWT required | Request; prefix stripped |
| Any | `/event/*` | JWT required | Event; prefix stripped |
| Any | `/attendance/*` | JWT required | Attendance; prefix stripped |
| Any | `/notification/*` | JWT required | Notification; prefix stripped |
| Any | `/members/*` | JWT required | Member; prefix stripped |
| Any | `/library/*` | JWT required | Library; prefix stripped |

### Registration and login

| Method | Gateway path | Direct path | Access |
| --- | --- | --- | --- |
| POST | `/register/register` | `http://localhost:5001/register` | Public |
| POST | `/auth/login` | `http://localhost:5002/login` | Public |

Registration requires `name`, `emailid`, `pass`, and `mobile`; public registration always creates role `user` and ignores supplied `role`. Provision admins through controlled database access using `npm run provision-admin` with `ADMIN_NAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `ADMIN_MOBILE` set in the registration service environment. Login requires `emailid`, `pass`, and `role`, and returns JWT valid for one hour.

### Request service

Gateway base: `/request`

Direct base: `http://localhost:8000`

| Method | Relative path | Access and behavior |
| --- | --- | --- |
| GET | `/health` | Direct route public; gateway route JWT-protected |
| POST | `/leave-requests` | JWT; create request |
| GET | `/leave-requests` | JWT; list current user's requests |
| GET | `/leave-requests/{request_id}` | JWT; owned record only |
| PATCH | `/leave-requests/{request_id}` | JWT; pending record only |
| PATCH | `/leave-requests/{request_id}/cancel` | JWT; pending record only |
| POST | `/pre-scholarship-registrations` | JWT; create registration |
| GET | `/pre-scholarship-registrations` | JWT; list current user's registrations |

Pre-scholarship get-one, update, and cancel handlers are disabled in source and are not API routes.

### Event service

Gateway base: `/event`

Direct base: `http://localhost:8001`

| Method | Relative path | Access and behavior |
| --- | --- | --- |
| POST | `/events` | Admin; create event |
| GET | `/events` | Authenticated; non-admin users receive published events |
| GET | `/events/{event_id}` | Authenticated; non-admin users can view published events |
| PATCH | `/events/{event_id}` | Admin; update event |
| DELETE | `/events/{event_id}` | Admin; delete event and referenced images |

Image upload and removal handlers are disabled. Existing uploaded files remain available directly under `/uploads/*`; gateway access through `/event/uploads/*` requires JWT.

### Attendance service

Gateway base: `/attendance`

Direct base: `http://localhost:8002`

| Method | Relative path | Access and behavior |
| --- | --- | --- |
| GET | `/health` | Direct public; gateway route JWT-protected |
| POST | `/check-in` | JWT; create current user's daily attendance |
| POST | `/check-out` | JWT; close current user's daily attendance |
| GET | `/me` | JWT; list current user's records |
| GET | `/` | Admin; list records with optional filters |
| PATCH | `/{id}` | Admin; update attendance record |

### Member service

Gateway API base: `/members/api/v1`

Direct API base: `http://localhost:8004/api/v1`

| Method | Relative path | Access and behavior |
| --- | --- | --- |
| GET | `/members/me` | JWT; get own profile, creating it from JWT claims on first use |
| PATCH | `/members/me` | JWT; update own `full_name`, `phone`, `address`, or `date_of_birth` |
| POST | `/members/me/documents` | JWT; upload own PDF, JPEG, PNG, or WEBP document as multipart form data |
| GET | `/members/me/documents` | JWT; list own documents; optional `doc_type`, `skip`, and `limit` |
| GET | `/members/me/documents/{document_id}/download` | JWT; download own document |
| GET | `/members` | Admin; list profiles; optional `q`, `role`, `skip`, and `limit` |
| GET | `/members/{user_id}` | Admin or matching user; get profile |
| GET | `/members/{user_id}/documents` | Admin or matching user; list documents |
| GET | `/members/{user_id}/documents/{document_id}/download` | Admin or matching user; download document |

List endpoints return total matching records in `X-Total-Count`. `user_id` is the JWT `id` claim, not the member document's MongoDB ID. Documents are private and have no static file route. Health check uses `/members/health` through the gateway or `http://localhost:8004/health` directly.

### Library service

Gateway API base: `/library/api/v1`

Direct API base: `http://localhost:8003/api/v1`

| Method | Relative path | Access and behavior |
| --- | --- | --- |
| POST | `/rooms` | Admin; create room |
| GET | `/rooms` | JWT; list rooms; optional `q`, `min_capacity`, `amenity`, `skip`, and `limit`; admin may also use `is_active` |
| GET | `/rooms/{room_id}` | JWT; get visible room |
| GET | `/rooms/{room_id}/availability` | JWT; list approved busy slots; required `start` and `end`, maximum 31-day window |
| PATCH | `/rooms/{room_id}` | Admin; update room or set `is_active` |
| DELETE | `/rooms/{room_id}` | Admin; delete room only when no booking history exists |
| POST | `/bookings` | JWT; create room booking |
| GET | `/bookings/me` | JWT; list own bookings; optional `status`, `upcoming`, `skip`, and `limit` |
| GET | `/bookings` | Admin; list booking history; optional `status`, `room_id`, `user_id`, `start_from`, `start_to`, `skip`, and `limit` |
| GET | `/bookings/{booking_id}` | Owner or admin; get booking |
| POST | `/bookings/{booking_id}/cancel` | Owner or admin; cancel pending or approved future booking |
| POST | `/bookings/{booking_id}/approve` | Admin; approve pending booking; optional `note` body |
| POST | `/bookings/{booking_id}/reject` | Admin; reject pending booking; optional `note` body |
| POST | `/books` | Admin; create catalog book |
| GET | `/books` | JWT; browse catalog; optional `q`, `category`, `skip`, and `limit` |
| GET | `/books/{book_id}` | JWT; get book |
| PATCH | `/books/{book_id}` | Admin; update book |
| DELETE | `/books/{book_id}` | Admin; delete book |

List endpoints return total matching records in `X-Total-Count`. Only approved bookings reserve time. Health check uses `/library/health` through the gateway or `http://localhost:8003/health` directly.

### Notification service

Gateway base: `/notification/api/v1`

Direct base: `http://localhost:8005/api/v1`

| Method | Relative path | Access and behavior |
| --- | --- | --- |
| GET | `/notifications` | JWT; list accessible notifications. Optional `type`, `read`, `skip`, and `limit`. |
| GET | `/notifications/unread-count` | JWT; return current user's unread count. |
| GET | `/notifications/{notification_id}` | JWT; return accessible notification. |
| PATCH | `/notifications/read-all` | JWT; mark all accessible unread notifications read. |
| PATCH | `/notifications/{notification_id}/read` | JWT; mark accessible notification read. |
| DELETE | `/notifications/{notification_id}` | JWT; hide notification for current user. |
| GET | `/notification-preferences/me` | JWT; get current user's notification preferences. |
| PATCH | `/notification-preferences/me` | JWT; update `inAppEnabled` and/or `mutedTypes`. |

`POST /internal/events` is service-to-service ingestion. It requires `x-internal-api-key`, accepts `event_id`, supported `type`, one of `recipient_id` or `recipient_role`, and optional object `data`, then returns `202`. Do not expose this route through public gateway.
