# API Contract

Gateway health, registration, and login are public. Every `/request/*`, `/event/*`, `/attendance/*`, and `/notification/*` gateway request requires `Authorization: Bearer <token>`. Use `http://localhost` through Nginx. Direct service exposure bypasses gateway authentication, but protected service handlers still enforce their own JWT dependencies.

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

### Registration and login

| Method | Gateway path | Direct path | Access |
| --- | --- | --- | --- |
| POST | `/register/register` | `http://localhost:5001/register` | Public |
| POST | `/auth/login` | `http://localhost:5002/login` | Public |

Registration requires `name`, `emailid`, `pass`, and `mobile`; `role` defaults to `user`. Login requires `emailid`, `pass`, and `role`, and returns JWT valid for one hour.

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
