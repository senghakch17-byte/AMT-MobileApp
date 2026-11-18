# OMS API Contract

Use `http://localhost` through Nginx. Protected endpoints require `Authorization: Bearer <token>`. Gateway health and every service health endpoint are public.

| Service | Gateway endpoints | Access |
| --- | --- | --- |
| Gateway | `GET /health` | Public |
| Registration | `GET /register/health`, `POST /register` | Public; registration always creates a `user` account |
| Login | `GET /login/health`, `POST /login` | Public |
| Requests | `GET /request/health`, `POST,GET /request/leave-requests`, `GET,PATCH /request/leave-requests/{id}`, `POST /request/leave-requests/{id}/approve`, `POST /request/leave-requests/{id}/reject`, `PATCH /request/leave-requests/{id}/cancel` | JWT; administrators get all requests and may approve or reject |
| Announcements | `GET /announcement/health`, `POST,GET /announcement`, `GET /announcement/all`, `GET,PATCH,DELETE /announcement/{id}` | JWT; `/all` and writes require admin; other users see published records only |
| Attendance | `GET /attendance/health`, `POST /attendance/check-in`, `POST /attendance/check-out`, `GET /attendance/me`, `POST,GET /attendance`, `GET,PATCH,DELETE /attendance/{id}` | JWT; administrative records require admin |
| Notifications | `GET /notification/health`, `POST,GET /notification`, `GET /notification/unread-count`, `PATCH /notification/read-all`, `GET,PATCH,DELETE /notification/{id}`, `PATCH /notification/{id}/read`, `GET,PATCH /notification/preferences/me` | JWT; create/update require admin |
| Users | `GET /user/health`, `GET,PATCH /user/me`, `POST,GET /user/me/documents`, `GET /user/me/documents/{id}/download`, `POST,GET /user`, `GET,PATCH,DELETE /user/{id}`, `GET /user/{id}/documents`, `GET /user/{id}/documents/{id}/download` | JWT; administrators manage accounts and profiles; user self-edits are limited to profile fields |
| Booking | `GET /booking/health`, `POST,GET /booking`, `GET /booking/me`, `GET /booking/{id}`, `POST /booking/{id}/cancel`, `POST /booking/{id}/approve`, `POST /booking/{id}/reject`, and `/booking/rooms/*` | JWT; room writes, booking list, approval, and rejection require admin |

## Workflow notes

- Leave requests start `pending`; an administrator can approve or reject them, and owners can cancel a pending request. Approval and rejection publish in-app notifications.
- Room bookings start `pending`; only approved bookings reserve a room time slot.
- Public `/register` ignores any supplied role and creates only `user` accounts.
- Notification ingestion remains private: `POST /internal/events` is called directly by trusted services with `x-internal-api-key`; it is not routed through the gateway.
- User administration calls Registration's private `/internal/users` routes using the same internal API key. Account deactivation blocks future login and soft-deletes the public profile.
- Deleting a room deactivates it; existing bookings remain available for audit history.
- Pre-scholarship registration and the book catalog are removed. Existing MongoDB documents are not deleted by this change.
