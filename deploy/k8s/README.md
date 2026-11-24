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

### LoadBalancer access with the Docker driver

The `nginx` Service is a `LoadBalancer`. If its external IP remains `<pending>`, or the Minikube IP cannot be reached from the host, run the following in a separate terminal and keep it running:

```bash
minikube tunnel
```

The tunnel may require administrator access. After it assigns an external IP, inspect it with `kubectl get service nginx -n oms` and map `oms.aupp.local` to that IP in `/etc/hosts`. This reaches Nginx directly; retain the Minikube-IP mapping when testing the configured Ingress route.

`secret.yaml` is intentionally ignored and is applied separately. Do not commit credentials.

## Requirement evidence

- **Load balancing:** run the health request repeatedly and capture distinct `X-Gateway-Instance` values.
- **Shared volume:** Nginx writes `/shared-logs/access.log`; the `log-reader` sidecar tails that same `emptyDir` volume. Verify with `kubectl logs -n oms deployment/nginx -c log-reader`.
- **Persistent data:** `announcement-uploads` and `user-uploads` PVCs back their respective services.
- **Cloud database:** verify a request created through `http://oms.aupp.local` appears in the configured MongoDB deployment.

## Remove

```bash
kubectl delete -k deploy/k8s
```
