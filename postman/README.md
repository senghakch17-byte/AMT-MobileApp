# Postman verification

Import `OMS-Backend.postman_collection.json` and `OMS-local.postman_environment.json` into Postman. Select the **OMS Minikube configuration** environment and set `gatewayUrl` to `http://oms.aupp.local` after the Minikube deployment is available.

Use this collection only through the public gateway URL. Do not test business services directly. Gateway health requests verify the Nginx-added `X-Upstream` header, because the public Ingress does not expose the upstream `Server` header. Login scripts save `userToken` and `adminToken` plus response-driven IDs as collection variables, so they do not depend on an active environment.

## Automated document upload

The document-upload request uses the included `fixtures/test-document.pdf`. In the Postman desktop app, set **Settings → Working directory** to this repository's `postman/` directory once. Postman then resolves the saved relative path automatically in individual requests and collection runs. Keep the `file` field type as **File** and do not set `Content-Type` manually.
