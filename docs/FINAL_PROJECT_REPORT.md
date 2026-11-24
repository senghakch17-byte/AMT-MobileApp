# OMS Final Project Report

## 1. Overview

OMS is a microservice backend for registration, login, leave requests, announcements, attendance, notifications, user profiles/documents, and room booking. It is deployed locally with Minikube using Kubernetes YAML and connects to an external MongoDB deployment.

## 2. Architecture

Clients use the Fanout DNS hostname `oms.aupp.local`. Kubernetes Ingress forwards to Nginx, which forwards all requests to the `api-gateway` Service. The API Gateway Deployment has two replicas and routes requests to ClusterIP-only business Services. Redis is internal. MongoDB is external and configured through a Kubernetes Secret.

Add the final architecture diagram in `evidence/01-architecture/`.

## 3. Kubernetes infrastructure

All Kubernetes resources are YAML under `deploy/k8s/`: namespace, ConfigMaps, Secret template, PVCs, Ingress, and a Deployment plus Service for every component. Deploy from the repository root:

```bash
minikube start
minikube addons enable ingress
./scripts/build-minikube-images.sh
cp deploy/k8s/config/secret.example.yaml deploy/k8s/config/secret.yaml
# Set cloud MongoDB and shared secret values in secret.yaml.
kubectl apply -f deploy/k8s/config/secret.yaml
kubectl apply -k deploy/k8s
echo "$(minikube ip) oms.aupp.local" | sudo tee -a /etc/hosts
kubectl get deployments,pods,services,ingress,pvc -n oms
```

Add `kubectl` resource screenshots in `evidence/02-kubernetes-resources/`.

## 4. Networking and load balancing

Ingress host `oms.aupp.local` is mapped to the Minikube IP. Nginx is the only public application entry point. Nginx forwards to the `api-gateway` ClusterIP Service, which balances requests between two gateway Pods. Capture repeated `/health` responses with distinct `X-Gateway-Instance` headers in `evidence/05-fanout-dns/`.

## 5. Database and storage

MongoDB is a cloud-hosted external dependency; no database container is deployed. Sensitive database and JWT configuration is supplied through an uncommitted Kubernetes Secret. Announcement and user-document uploads use PVCs. Nginx and its `log-reader` sidecar share an `emptyDir` log volume, demonstrating multi-container shared storage.

Add cloud database and shared-volume evidence in `evidence/04-cloud-database/` and `evidence/06-shared-volume/`.

## 6. Functional testing

The Postman collection in `docs/postman/` sends requests through `http://oms.aupp.local`. Include registration/login, authenticated routes, authorization rejection, and persistence evidence in `evidence/07-api-testing/`.

## 7. Challenges and solutions

| Challenge | Resolution |
| --- | --- |
| Local images unavailable to Minikube | Build each image with `scripts/build-minikube-images.sh`. |
| DNS name unavailable locally | Map `oms.aupp.local` to `minikube ip`. |
| External database credentials | Supply them only in `deploy/k8s/config/secret.yaml`. |
| Demonstrating shared data | Use Nginx and `log-reader` sidecar logs from the shared volume. |

## 8. Team contributions

Complete this table before submission.

| Member | Contribution | Evidence |
| --- | --- | --- |
| | | |

## 9. Conclusion

Complete after the Minikube demonstration. State only verified results, link the supporting evidence, and note any known limitations.
