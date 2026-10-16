# Troubleshooting

### `Application startup failed`

```bash
docker compose logs --tail=200 request-service event-service
```

Confirm MongoDB URI, credentials, database name, network access, and DNS connectivity.

### `Bad Gateway`

```bash
docker compose ps
docker compose logs --tail=200 api-gateway
```

Confirm target service and gateway service URL.

### `401 Access Denied`

Use token returned by `/auth/login` in exact `Authorization: Bearer <token>` header. All token-verifying services must share `JWT_SECRET`.
