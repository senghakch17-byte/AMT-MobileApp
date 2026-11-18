# Configuration

From repository root, copy each template and replace placeholder values:

```bash
cp apps/registration-service/.env.example apps/registration-service/.env
cp apps/attendance-service/.env.example apps/attendance-service/.env
cp apps/login-service/.env.example apps/login-service/.env
cp apps/request-service/.env.example apps/request-service/.env
cp apps/announcement-service/.env.example apps/announcement-service/.env
cp apps/notification-service/.env.example apps/notification-service/.env
cp apps/user-service/.env.example apps/user-service/.env
cp apps/booking-service/.env.example apps/booking-service/.env
cp apps/api-gateway/.env.example apps/api-gateway/.env
```

Registration, login, attendance, and notification services require `MONGO_URI`. Login, attendance, and notification services require `JWT_SECRET`. Notification service requires `INTERNAL_API_KEY` for service-to-service announcement ingestion. Announcement and attendance producers require matching `INTERNAL_API_KEY` plus `NOTIFICATION_SERVICE_URL`; Compose sets URL to `http://notification-service:8005`. Request, announcement, user, and booking services require `MONGODB_URI`, `MONGODB_DB_NAME`, `JWT_SECRET`, and `JWT_ALGORITHM`. Gateway requires every service URL, including `USER_SERVICE_URL`, `BOOKING_SERVICE_URL`, and `NOTIFICATION_SERVICE_URL`, and same `JWT_SECRET` used by login and protected services.

Public registration creates role `admin` only for exact request value `role: "admin"`; all other or missing values create role `user`. This allows public self-provisioning of administrator accounts. To provision admin from environment values, set `ADMIN_NAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `ADMIN_MOBILE` in `apps/registration-service/.env`, then run `cd apps/registration-service && npm run provision-admin`.

Announcement image URLs should use gateway prefix:

```dotenv
PUBLIC_BASE_URL=http://localhost/announcement
UPLOAD_DIR=uploads
MAX_IMAGE_MB=5
MAX_IMAGES_PER_ANNOUNCEMENT=10
```

Do not commit `.env` files or credentials. URL-encode reserved characters in MongoDB passwords.
