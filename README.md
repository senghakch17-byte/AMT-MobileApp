# OMS Microservice Backend

OMS is a Kubernetes-based microservice backend for registration and login, leave requests, announcements, attendance, notifications, user profiles/documents, and room booking. It runs on Minikube and uses an external MongoDB deployment.

## Architecture

```text
Client
  |
  v
http://oms.aupp.local
  |
  v
Kubernetes Ingress -> Nginx -> API Gateway Service -> 2 API Gateway Pods
                                                   |
                                                   v
                                     Internal ClusterIP business services
                                                   |             |
                                                   v             v
                                         External MongoDB      Redis
```

All client traffic must use the public Ingress hostname. Nginx is the public reverse proxy; the API Gateway validates JWTs and routes requests to internal services. Each business service enforces its own roles, ownership, and business authorization. Business-service Services are `ClusterIP` only and are not public entry points.

## Services

| Service | Responsibility | Container port |
| --- | --- | ---: |
| Nginx | Internal reverse proxy and shared-log producer | 80 |
| API Gateway | Routing and JWT middleware | 4000 |
| Registration | Account creation and password hashing | 5001 |
| Login | Credential validation and JWT issuance | 5002 |
| Request | Leave-request workflow | 8000 |
| Announcement | Announcement management and uploads | 8001 |
| Attendance | Multiple daily check-in/out sessions and corrections | 8002 |
| Booking | Room and booking workflow | 8003 |
| User | Profiles and document history | 8004 |
| Notification | In-app notifications and receipt state | 8005 |
| Redis | Internal event transport | 6379 |

Public gateway prefixes are `/register`, `/login`, `/request`, `/announcement`, `/attendance`, `/notification`, `/user`, `/booking`, and `/health`.

## Prerequisites

- Docker
- Minikube
- `kubectl`
- A reachable external MongoDB deployment
- Permission to add a local `/etc/hosts` entry

## Deploy to Minikube

Run every command below from the repository root.

### 1. Start the cluster and enable Ingress

```bash
minikube start
minikube addons enable ingress
```

### 2. Build application images in Minikube

```bash
./scripts/build-minikube-images.sh
```

The script builds the gateway and all application-service images in Minikube's image store. The Kubernetes Deployments use `imagePullPolicy: IfNotPresent`, so no remote registry is required.

### 3. Create the namespace and Secret

```bash
kubectl apply -f deploy/k8s/cluster/namespace.yaml
cp deploy/k8s/config/secret.example.yaml deploy/k8s/config/secret.yaml
```

Edit `deploy/k8s/config/secret.yaml` and replace every placeholder. Supply a valid MongoDB URI and shared secret values:

- `MONGO_URI` for Node.js services
- `MONGODB_URI` for Python services
- `JWT_SECRET` shared by the login service, gateway, and protected services
- `INTERNAL_API_KEY` shared by internal event producers and the notification service

`secret.yaml` is ignored by Git. Never commit credentials, tokens, database URIs, or secrets.

Apply the Secret:

```bash
kubectl apply -f deploy/k8s/config/secret.yaml
```

### 4. Deploy OMS

```bash
kubectl apply -k deploy/k8s
kubectl get deployments,pods,services,ingress,pvc -n oms
```

Wait until application Pods are ready:

```bash
kubectl get pods -n oms --watch
```

Use `Ctrl+C` to stop watching after all Pods report `Running` and ready containers.

### 5. Configure the local hostname and verify

For the Ingress route, map the hostname to the Minikube IP:

```bash
echo "$(minikube ip) oms.aupp.local" | sudo tee -a /etc/hosts
curl -i http://oms.aupp.local/health
```

#### macOS/Docker driver: expose Ingress

If the Minikube IP is not reachable from the host, run this command in a separate terminal and keep it running:

```bash
sudo minikube tunnel
```

The tunnel exposes the public Ingress on `127.0.0.1`. Replace the Minikube-IP hostname mapping with:

```bash
sudo sed -i '' '/oms\.aupp\.local/d' /etc/hosts
echo "127.0.0.1 oms.aupp.local" | sudo tee -a /etc/hosts
```

Keep the tunnel running while accessing `http://oms.aupp.local`. The request path remains Ingress → Nginx → API Gateway.

Repeat the request to check that the two API Gateway replicas receive traffic:

```bash
for i in {1..8}; do
  curl -s -i http://oms.aupp.local/health | grep -i x-gateway-instance
done
```

## Kubernetes layout

```text
deploy/k8s/
  cluster/       Namespace definition
  config/        Shared ConfigMap and Secret template
  storage/       PersistentVolumeClaims for uploads
  networking/    Public Ingress
  components/    Deployment and Service YAML for every component
  kustomization.yaml
```

`kustomization.yaml` deploys all non-secret resources. Internal Services provide stable DNS names such as `api-gateway`, `request-service`, and `redis` to Pods in the `oms` namespace.

## Storage and event delivery

- MongoDB stores application data externally.
- `announcement-uploads` and `user-uploads` PersistentVolumeClaims preserve uploaded files.
- Redis has no disk persistence and is used for internal event transport.
- The Nginx `log-reader` sidecar reads access logs from the same `emptyDir` volume as Nginx.

Inspect the shared Nginx log volume after a public request:

```bash
kubectl logs -n oms deployment/nginx -c log-reader
```

## API testing

Import these files into Postman:

- `postman/OMS-Backend.postman_collection.json`
- `postman/OMS-local.postman_environment.json`

The environment defaults to `http://oms.aupp.local`. Test only through the public gateway URL; do not test business services or individual Gateway Pods directly. The document-upload request requires selecting a local PDF, JPEG, PNG, or WEBP file after import.

Read the [Postman verification guide](postman/README.md) for details.

## Verification

Run these static checks from the repository root:

```bash
kubectl kustomize deploy/k8s
bash -n scripts/build-minikube-images.sh
python3 -m json.tool postman/OMS-Backend.postman_collection.json >/dev/null
python3 -m json.tool postman/OMS-local.postman_environment.json >/dev/null
```

Runtime verification requires a real Minikube cluster, valid secrets, and reachable MongoDB. Kubernetes manifests alone do not prove deployment readiness.

## Cleanup

```bash
kubectl delete -k deploy/k8s
```

Removing the namespace also removes the separately applied Secret.

## Documentation

- [Kubernetes deployment guide](deploy/k8s/README.md)
- [Final project report](docs/FINAL_PROJECT_REPORT.md)
- [Screenshot checklist](docs/SCREENSHOT_CHECKLIST.md)
- [Postman verification](postman/README.md)

## Repository layout

```text
apps/                Application services and Dockerfiles
deploy/k8s/          Kubernetes manifests
scripts/             Minikube image-build helper
docs/                Project report, screenshot checklist, and Postman files
```
