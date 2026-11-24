# OMS Microservice Backend

OMS is a containerized backend for registration and login, leave requests, announcements, attendance, notifications, user profiles/documents, and room booking. It supports local development with Docker Compose and a Minikube Kubernetes deployment. MongoDB is external in both environments; this repository does not provision a MongoDB container.

## Architecture

```text
Client
  |
  +-- Docker Compose: http://localhost
  |       |
  |       v
  |     Nginx -> API Gateway (2 replicas) -> internal services
  |
  +-- Kubernetes: http://oms.aupp.local
          |
          v
        Ingress -> Nginx -> API Gateway (2 replicas) -> ClusterIP services
                                                        |       |
                                                        v       v
                                                 External MongoDB Redis
```

Nginx is the public entry point. The API Gateway routes requests to the application services and applies gateway authentication. Kubernetes business services are private `ClusterIP` Services and are not public entry points.

## Services

| Service | Responsibility | Container port |
| --- | --- | ---: |
| Nginx | Public reverse proxy and gateway load balancer | 80 |
| API Gateway | Routing and JWT middleware | 4000 |
| Registration | Account creation and password hashing | 5001 |
| Login | Credential validation and JWT issuance | 5002 |
| Request | Leave-request workflow | 8000 |
| Announcement | Announcement management and uploads | 8001 |
| Attendance | Check-in, check-out, and corrections | 8002 |
| Booking | Room and booking workflow | 8003 |
| User | Profiles and document history | 8004 |
| Notification | In-app notifications and receipt state | 8005 |
| Redis | Internal event transport | 6379 |

Public gateway prefixes are `/register`, `/login`, `/request`, `/announcement`, `/attendance`, `/notification`, `/user`, `/booking`, and `/health`.

## Prerequisites

### Docker Compose

- Docker Desktop with Docker Compose
- A reachable MongoDB deployment
- Configuration and shared secrets for every service

### Kubernetes

- Docker, Minikube, and `kubectl`
- A reachable MongoDB deployment
- Permission to add an `/etc/hosts` entry

## Configure local Docker Compose

Each application service has an `.env.example` template. Copy every template to an untracked `.env` file, then set the required variables.

```bash
for file in apps/*/.env.example; do
  cp "$file" "${file%.example}"
done
```

At minimum, configure the MongoDB URI and shared JWT secret consistently for services that require them. Do not commit `.env` files, passwords, tokens, API keys, or MongoDB connection strings.

The Compose file injects internal service URLs, Redis URLs, and port values where needed. It exposes Nginx at port 80 and maps individual service ports for local troubleshooting only.

## Run with Docker Compose

From the repository root:

```bash
docker compose config
docker compose up --build
```

The public application URL is `http://localhost`.

Useful commands:

```bash
docker compose ps
docker compose logs -f api-gateway
docker compose logs -f request-service announcement-service
docker compose down
```

To remove named upload volumes too:

```bash
docker compose down -v
```

`depends_on` controls container startup order; it does not confirm that MongoDB or upstream services are ready.

## Deploy to Minikube

Kubernetes resources are in [`deploy/k8s/`](deploy/k8s/). The deployment uses locally built Minikube images, an Ingress hostname of `oms.aupp.local`, external MongoDB, Redis, and persistent volumes for uploads.

### 1. Start Minikube and enable Ingress

```bash
minikube start
minikube addons enable ingress
```

### 2. Build application images in Minikube

```bash
./scripts/build-minikube-images.sh
```

This builds the gateway and all application-service images in Minikube's image store. Kubernetes uses `imagePullPolicy: IfNotPresent`, so no remote image registry is required.

### 3. Create and apply the Kubernetes Secret

```bash
kubectl apply -f deploy/k8s/cluster/namespace.yaml
cp deploy/k8s/config/secret.example.yaml deploy/k8s/config/secret.yaml
```

Edit `deploy/k8s/config/secret.yaml` and replace every placeholder with a valid MongoDB URI and shared secrets. The file is ignored by Git and must not be committed.

```bash
kubectl apply -f deploy/k8s/config/secret.yaml
```

### 4. Deploy OMS

```bash
kubectl apply -k deploy/k8s
kubectl get deployments,pods,services,ingress,pvc -n oms
```

### 5. Configure local DNS and verify

```bash
echo "$(minikube ip) oms.aupp.local" | sudo tee -a /etc/hosts
curl -i http://oms.aupp.local/health
```

Repeat the health request to observe gateway load balancing. Responses should eventually show distinct `X-Gateway-Instance` header values.

### Remove Kubernetes resources

```bash
kubectl delete -k deploy/k8s
```

See the [Kubernetes deployment guide](deploy/k8s/README.md) for resource-level details and evidence checks.

## Kubernetes layout

```text
deploy/k8s/
  cluster/       Namespace definition
  config/        Shared ConfigMap and Secret template
  storage/       PersistentVolumeClaims for uploads
  networking/    Public Ingress
  components/    Deployment and Service files for each component
  kustomization.yaml
```

`kustomization.yaml` applies all non-secret resources. Internal Services provide DNS names such as `api-gateway`, `request-service`, and `redis` to Pods in the `oms` namespace.

## Storage and events

- MongoDB stores application data externally.
- `announcement-uploads` and `user-uploads` PersistentVolumeClaims preserve uploaded files in Kubernetes.
- Redis has no disk persistence and is used for internal event transport.
- The Nginx `log-reader` sidecar reads access logs from the same `emptyDir` volume as Nginx.

Inspect the shared log volume after a request:

```bash
kubectl logs -n oms deployment/nginx -c log-reader
```

## API testing

Import these files into Postman:

- `docs/postman/OMS-Backend.postman_collection.json`
- `docs/postman/OMS-local.postman_environment.json`

Use `http://localhost` for Docker Compose or `http://oms.aupp.local` for Minikube. Test through the public gateway rather than directly against business services. The document-upload request requires selecting `docs/postman/fixtures/user-test-document.pdf` after import.

Read the [Postman verification guide](docs/postman/README.md) for details.

## Verification

Run static checks from the repository root:

```bash
docker compose config
kubectl kustomize deploy/k8s
bash -n scripts/build-minikube-images.sh
python3 -m json.tool docs/postman/OMS-Backend.postman_collection.json >/dev/null
python3 -m json.tool docs/postman/OMS-local.postman_environment.json >/dev/null
```

Kubernetes runtime verification requires a real Minikube cluster, valid secrets, and reachable MongoDB. The manifests alone do not prove deployment readiness.

## Documentation

- [Kubernetes deployment guide](deploy/k8s/README.md)
- [Final project report](docs/FINAL_PROJECT_REPORT.md)
- [Screenshot checklist](docs/SCREENSHOT_CHECKLIST.md)
- [Postman verification](docs/postman/README.md)

## Repository layout

```text
apps/                Application services and Dockerfiles
nginx/               Docker Compose Nginx configuration
deploy/k8s/          Kubernetes manifests
scripts/             Minikube image-build helper
docs/                Project report, evidence folders, and Postman files
docker-compose.yaml  Local orchestration
```
