# Final demonstration screenshot checklist

Store readable, redacted screenshots in the matching `docs/evidence/` folder. Do not include credentials, full JWTs, or MongoDB URIs.

- [ ] `01-architecture`: current architecture diagram showing Ingress, Nginx, API Gateway, services, external MongoDB, Redis, and volumes.
- [ ] `02-kubernetes-resources`: `minikube status` and `kubectl get deployments,pods,services,ingress,pvc -n oms`.
- [ ] `03-api-gateway`: public request through `http://oms.aupp.local`; direct business-service access is not used.
- [ ] `04-cloud-database`: a record created through the public API and visible in cloud MongoDB.
- [ ] `05-fanout-dns`: `/etc/hosts` mapping and repeated health responses with different `X-Gateway-Instance` values.
- [ ] `06-shared-volume`: Nginx request log shown by the `log-reader` sidecar.
- [ ] `07-api-testing`: Postman collection results, including authentication and a protected API.
- [ ] `08-team-contributions`: contribution table and each member's implementation evidence.
