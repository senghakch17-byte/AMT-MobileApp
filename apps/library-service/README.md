# Library Service

FastAPI + MongoDB (Beanie) service for **room booking** and the **book catalog**.
Same layout and conventions as `event-service` / `member-service`: JWT bearer tokens issued
elsewhere (`id`, `emailid`, `role` claims), routed through the gateway under `/library`.

## Endpoints (`/api/v1`)

### Rooms
| Method | Path | Who | What |
|---|---|---|---|
| POST | `/rooms` | **admin** | Add a room (`name`, `location`, `capacity`, `amenities`, `description`) |
| PATCH | `/rooms/{id}` | **admin** | Edit room information, or deactivate it with `is_active: false` |
| DELETE | `/rooms/{id}` | **admin** | Delete a room (refused if it has booking history; deactivate instead) |
| GET | `/rooms` | any user | List rooms (`q`, `min_capacity`, `amenity`, `skip`, `limit`; admins also `is_active`) |
| GET | `/rooms/{id}` | any user | Room details |
| GET | `/rooms/{id}/availability?start=&end=` | any user | Approved (busy) slots in a window of up to 31 days; no user details |

Users only see active rooms; admins see all.

### Bookings
| Method | Path | Who | What |
|---|---|---|---|
| POST | `/bookings` | any user | Book a room (`room_id`, `start_at`, `end_at`, `attendees`, `purpose`) |
| GET | `/bookings/me` | any user | Own bookings (`status`, `upcoming`) |
| GET | `/bookings/{id}` | owner or admin | One booking (others get 404) |
| POST | `/bookings/{id}/cancel` | owner or admin | Cancel a pending/approved booking that hasn't started |
| GET | `/bookings` | **admin** | Booking history (`status`, `room_id`, `user_id`, `start_from`, `start_to`); `status=pending` is the approval queue |
| POST | `/bookings/{id}/approve` | **admin** | Approve a pending booking (optional `{"note": "..."}`) |
| POST | `/bookings/{id}/reject` | **admin** | Reject a pending booking (optional `{"note": "..."}`) |

### Books
| Method | Path | Who | What |
|---|---|---|---|
| POST / PATCH / DELETE | `/books`, `/books/{id}` | **admin** | Manage the catalog |
| GET | `/books` | any user | Browse (`q` title/author, `category`, `skip`, `limit`) |
| GET | `/books/{id}` | any user | Book details |

List endpoints return the total in an `X-Total-Count` header. `GET /health` is public.

## Booking rules

- Statuses: `pending` → `approved` / `rejected`; `pending` or `approved` → `cancelled`.
- **Approval is optional.** `REQUIRE_BOOKING_APPROVAL=true` (default): bookings start `pending` until an
  admin approves. `false`: a booking is approved immediately if the slot is free.
- Only **approved** bookings hold a room. Several users can have pending requests for the same slot;
  once the admin approves one, the others can only be rejected.
- A booking must start in the future, last between `MIN_BOOKING_MINUTES` (30) and
  `MAX_BOOKING_HOURS` (4), and not exceed the room's capacity.
- A user can't hold two overlapping pending/approved bookings (that would block several rooms at once).
- Back-to-back bookings are fine (end time is exclusive).
- Times are stored in UTC; a time without an offset is treated as UTC.
- Mongo can't enforce "no overlapping ranges" with an index, so approval checks, writes, then checks again;
  in a rare race both requests back out rather than ever double-booking the room.

## Development setup with `uv`

```bash
uv sync
cp .env.example .env        # set MONGODB_URI and the same JWT_SECRET as the auth service
uv run uvicorn app.main:app --reload --port 8003
```

Swagger UI: http://localhost:8003/docs

## Tests

```bash
uv run pytest                                              # no-database tests; DB tests skip
MONGODB_TEST_URI=mongodb://localhost:27017 uv run pytest   # also runs the end-to-end DB tests
```

DB tests use a throwaway database named `library_service_test`.

## Docker

```bash
docker build -t library-service .
docker run -p 8003:8003 --env-file .env library-service
```
