# OMS Microservice Backend

OMS is a containerized backend for registration, login, leave requests, announcements, attendance, notifications, user profiles/documents, and room booking. It supports local Docker Compose development and Minikube Kubernetes deployment. MongoDB is external in both environments.

## Architecture

```text
Client -> oms.aupp.local -> Kubernetes Ingress -> Nginx -> API Gateway (2 replicas)
                                                          -> internal microservices -> external MongoDB
                                                          -> Redis
```

All public application requests use Nginx and the API Gateway. Business services are internal in Kubernetes.

## Docker Compose

Copy each service `.env.example` to `.env` and set the required cloud MongoDB URI plus shared secrets. Then run:

```bash
docker compose config
docker compose up --build
```

The local public URL is `http://localhost`. Stop the stack with `docker compose down`.

## Kubernetes with Minikube

The YAML-only Kubernetes configuration is in `deploy/k8s/`. See [the Kubernetes deployment guide](deploy/k8s/README.md) for the required Minikube, secret, image-build, Fanout DNS, verification, and cleanup commands.

## Final project evidence

- [Final project report](docs/FINAL_PROJECT_REPORT.md)
- [Screenshot checklist](docs/SCREENSHOT_CHECKLIST.md)
- [Postman verification](docs/postman/README.md)

## Repository layout

```text
apps/          microservice source code and Dockerfiles
nginx/         local Docker Compose load balancer
deploy/k8s/    Kubernetes resources organized by cluster, config, storage, networking, and component
scripts/       Minikube image-build helper
docs/          final report, evidence folders, and Postman verification files
```
