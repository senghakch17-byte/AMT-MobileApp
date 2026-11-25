# OMS Kubernetes deployment

This directory contains the YAML-only Minikube deployment for OMS. Every client request enters through the `oms.aupp.local` Ingress, reaches Nginx, then the two-replica API Gateway Service. Business-service Services are ClusterIP-only and are not public entry points. MongoDB is external and must be supplied through a Kubernetes Secret.

## Layout

- `cluster/` — namespace
- `config/` — shared ConfigMap and secret template
- `storage/` — persistent-volume claims for application uploads
- `networking/` — the public Ingress
- `components/<name>/` — separate Deployment and Service YAML for each component

## Prerequisites

- Docker, Minikube, and `kubectl`
- A reachable cloud MongoDB deployment
- A local `/etc/hosts` entry for the Fanout DNS hostname

## Deploy

```bash
minikube start
minikube addons enable ingress
./scripts/build-minikube-images.sh
kubectl apply -f deploy/k8s/cluster/namespace.yaml
cp deploy/k8s/config/secret.example.yaml deploy/k8s/config/secret.yaml
# Edit deploy/k8s/config/secret.yaml with cloud MongoDB and shared secret values.
kubectl apply -f deploy/k8s/config/secret.yaml
kubectl apply -k deploy/k8s
echo "$(minikube ip) oms.aupp.local" | sudo tee -a /etc/hosts
kubectl get deployments,pods,services,ingress -n oms
curl -i http://oms.aupp.local/health
```

### Ingress access with the Docker driver

If the Minikube IP cannot be reached from the host, run the following in a separate terminal and keep it running:

```bash
sudo minikube tunnel
```

The tunnel exposes the public Ingress on `127.0.0.1`. Replace the Minikube-IP mapping with `127.0.0.1 oms.aupp.local` in `/etc/hosts`, then verify `curl -i http://oms.aupp.local/health`. The nginx Service remains internal (`ClusterIP`); Ingress is the only public entry point.

`secret.yaml` is intentionally ignored and is applied separately. Do not commit credentials.

The shared ConfigMap sets `ATTENDANCE_TIME_ZONE=Asia/Phnom_Penh`; attendance sessions are grouped by that local calendar day.

## Requirement evidence

- **Load balancing:** run the health request repeatedly and capture distinct `X-Gateway-Instance` values.
- **Shared volume:** Nginx writes `/shared-logs/access.log`; the `log-reader` sidecar tails that same `emptyDir` volume. Verify with `kubectl logs -n oms deployment/nginx -c log-reader`.
- **Persistent data:** `announcement-uploads` and `user-uploads` PVCs back their respective services.
- **Cloud database:** verify a request created through `http://oms.aupp.local` appears in the configured MongoDB deployment.

## Remove

```bash
kubectl delete -k deploy/k8s
```
