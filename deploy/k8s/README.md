# OMS Kubernetes manifests

These manifests target local Minikube. They do not create MongoDB; configure a reachable external MongoDB URI in the secret. A real deployment and screenshots still require a running Minikube cluster and valid secrets.

## Prerequisites

1. Start Minikube and enable Ingress: `minikube start && minikube addons enable ingress`.
2. Build every local application image into Minikube: `./scripts/build-minikube-images.sh`.
3. Copy `secret.example.yaml` to `secret.yaml`, set real values, and keep it uncommitted.
4. Ensure the cluster has a default StorageClass, or add `storageClassName` to the two PVCs.

## Apply

```bash
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/secret.yaml
kubectl apply -k deploy/k8s
kubectl get pods,svc -n oms
kubectl get ingress -n oms
```

## Fanout DNS

The Ingress host is `oms.aupp.local`. Map it to the Minikube IP:

```bash
echo "$(minikube ip) oms.aupp.local" | sudo tee -a /etc/hosts
curl -i http://oms.aupp.local/health
```

The repeated health request exposes `X-Gateway-Instance`; capture two distinct values to prove the two gateway replicas are serving traffic. If Ingress is unavailable, `minikube tunnel` may be needed for LoadBalancer access, but use the Ingress hostname for the required DNS demonstration.

## Topology

- Nginx is the public entry point.
- `api-gateway` has two replicas; its ClusterIP Service balances requests between them.
- Every application service and Redis uses a ClusterIP Service.
- Redis has no persistence, matching local Compose behavior.
- Announcement and user-document uploads use separate PVCs.
- Nginx writes access logs to a shared `emptyDir`; the `log-reader` sidecar reads the same file. Verify with `kubectl logs -n oms deployment/nginx -c log-reader` after making a request.
- `secret.yaml` is intentionally omitted from `kustomization.yaml`; apply it separately.
