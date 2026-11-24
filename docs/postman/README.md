# Postman verification

Import `OMS-Backend.postman_collection.json` and `OMS-local.postman_environment.json` into Postman. Set `gatewayUrl` to `http://oms.aupp.local` after the Minikube deployment is available.

Use this collection only through the public gateway URL. Do not test business services directly. The document-upload request requires selecting `fixtures/user-test-document.pdf` after import because Postman does not embed local file contents in its export.
