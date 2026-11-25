# Postman verification

Import `OMS-Backend.postman_collection.json` and `OMS-local.postman_environment.json` into Postman. Select the **OMS Minikube configuration** environment and set `gatewayUrl` to `http://oms.aupp.local` after the Minikube deployment is available.

Use this collection only through the public gateway URL. Do not test business services directly. Login scripts save `userToken` and `adminToken` plus response-driven IDs as collection variables, so they do not depend on an active environment. The document-upload request requires selecting a local PDF, JPEG, PNG, or WEBP file after import because Postman does not embed file contents in its export.
