# Configuration

From repository root, copy each template and replace placeholder values:

```bash
cp apps/registration-service/.env.example apps/registration-service/.env
cp apps/attendance-service/.env.example apps/attendance-service/.env
cp apps/login-service/.env.example apps/login-service/.env
cp apps/request-service/.env.example apps/request-service/.env
cp apps/event-service/.env.example apps/event-service/.env
cp apps/notification-service/.env.example apps/notification-service/.env
cp apps/api-gateway/.env.example apps/api-gateway/.env
```

Registration, login, attendance, and notification services require `MONGO_URI`. Login, attendance, and notification services require `JWT_SECRET`. Notification service also requires `INTERNAL_API_KEY` for service-to-service event ingestion. Request and event services require `MONGODB_URI`, `MONGODB_DB_NAME`, `JWT_SECRET`, and `JWT_ALGORITHM`. Gateway requires every service URL, including `NOTIFICATION_SERVICE_URL`, and same `JWT_SECRET` used by login and protected services.

Event image URLs should use gateway prefix:

```dotenv
PUBLIC_BASE_URL=http://localhost/event
UPLOAD_DIR=uploads
MAX_IMAGE_MB=5
MAX_IMAGES_PER_EVENT=10
```

Do not commit `.env` files or credentials. URL-encode reserved characters in MongoDB passwords.
