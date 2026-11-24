# Postman verification

Import `OMS-Backend.postman_collection.json` and `OMS-local.postman_environment.json (OMS Minikube gateway)` into Postman. Set `gatewayUrl` to `http://oms.aupp.local` after the Minikube deployment is available.

Use this collection only through the public gateway URL. Do not test business services directly. The document-upload request requires selecting a local PDF, JPEG, PNG, or WEBP file after import because Postman does not embed file contents in its export.
