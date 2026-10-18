# Configuration

From repository root, copy each template and replace placeholder values:

```bash
cp apps/registration-service/.env.example apps/registration-service/.env
cp apps/attendance-service/.env.example apps/attendance-service/.env
cp apps/login-service/.env.example apps/login-service/.env
cp apps/request-service/.env.example apps/request-service/.env
cp apps/event-service/.env.example apps/event-service/.env
cp apps/notification-service/.env.example apps/notification-service/.env
cp apps/member-service/.env.example apps/member-service/.env
cp apps/library-service/.env.example apps/library-service/.env
cp apps/api-gateway/.env.example apps/api-gateway/.env
```

Registration, login, attendance, and notification services require `MONGO_URI`. Login, attendance, and notification services require `JWT_SECRET`. Notification service also requires `INTERNAL_API_KEY` for service-to-service event ingestion. Request, event, member, and library services require `MONGODB_URI`, `MONGODB_DB_NAME`, `JWT_SECRET`, and `JWT_ALGORITHM`. Gateway requires every service URL, including `MEMBER_SERVICE_URL`, `LIBRARY_SERVICE_URL`, and `NOTIFICATION_SERVICE_URL`, and same `JWT_SECRET` used by login and protected services.

Public registration always creates role `user`. To create controlled demo admin in a non-production database, set `ADMIN_NAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `ADMIN_MOBILE` in `apps/registration-service/.env`, then run `cd apps/registration-service && npm run provision-admin`.

Event image URLs should use gateway prefix:

```dotenv
PUBLIC_BASE_URL=http://localhost/event
UPLOAD_DIR=uploads
MAX_IMAGE_MB=5
MAX_IMAGES_PER_EVENT=10
```

Do not commit `.env` files or credentials. URL-encode reserved characters in MongoDB passwords.
