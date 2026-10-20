# Notification Service

Express service that stores in-app notifications in MongoDB and consumes trusted notification events from a Redis Stream.

## Configuration

Copy `.env.example` to `.env`, then configure the MongoDB URI, the same JWT secret used by the login service, Redis, and `INTERNAL_API_KEY`.

## User API

All user routes require `Authorization: Bearer <token>`. Through the gateway, prefix these paths with `/notification`.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/v1/notifications` | List a user's direct and role-targeted notifications. Supports `skip`, `limit`, `read=true|false`, and `type`. |
| GET | `/api/v1/notifications/unread-count` | Get unread count. |
| GET | `/api/v1/notifications/{id}` | Get one accessible notification. |
| PATCH | `/api/v1/notifications/{id}/read` | Mark one notification read. |
| PATCH | `/api/v1/notifications/read-all` | Mark all accessible notifications read. |
| DELETE | `/api/v1/notifications/{id}` | Hide one accessible notification for current user. |
| GET | `/api/v1/notification-preferences/me` | Get in-app notification preferences. |
| PATCH | `/api/v1/notification-preferences/me` | Update `inAppEnabled` and/or supported `mutedTypes`. |

## Event ingestion

The consumer group reads from `notification:events` by default. Events must contain:

```json
{
  "event_id": "event-service:65e...:published",
  "type": "event.published",
  "recipient_role": "user",
  "data": { "event_id": "65e...", "screen": "event-details" }
}
```

Supported event types are `request.approved`, `request.rejected`, `attendance.absent`, `attendance.corrected`, `event.published`, and `event.updated`. The service owns message templates; producers only provide trusted event metadata.

Event service publishes `event.published` when an event becomes published and `event.updated` for later published-event changes. Attendance service publishes `attendance.absent` when an admin marks a record absent, otherwise `attendance.corrected` after an admin correction. Both call `POST /api/v1/internal/events` directly with `x-internal-api-key`; it is not exposed for mobile clients. Producer delivery has a three-second timeout and does not roll back completed source writes; retry failed deliveries from an outbox when guaranteed delivery is required.

At-least-once Redis delivery is made idempotent using a unique `event_id` plus recipient constraint.

## Read and delete state

Notification documents stay shared for role-targeted delivery. Per-user `NotificationReceipt` documents store `readAt` and `deletedAt`, keyed uniquely by notification ID plus user ID. Marking or hiding notification never changes another recipient's state or removes shared notification.
