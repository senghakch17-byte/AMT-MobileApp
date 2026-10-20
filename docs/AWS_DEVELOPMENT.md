# AWS Sandbox Development

This guide targets temporary AWS Academy, Learner Lab, or student sandbox accounts. It is for development and course demonstrations, not production deployment.

## Sandbox limits

- Start lab session before using AWS Console, CLI, or temporary credentials.
- Sandbox credentials, instances, public IPs, and permissions can expire or reset.
- Use lab-provided region, VPC, subnet, and IAM role. Do not create resources blocked by sandbox policy.
- Monitor AWS Academy credits. Stop or terminate resources after testing.
- Do not store AWS credentials, private keys, JWT secrets, MongoDB URIs, or service `.env` files in this repository.

## Recommended first deployment

Use one Ubuntu EC2 instance and root `docker-compose.yaml` first. It runs all active local services together and costs less than multi-host deployment.

```text
Internet
   |
EC2 instance
   |- Nginx :80
   |- API gateways :4000, :4001
   |- Application services
   `- Redis :6379
   |
External MongoDB
```

This repository does not provision MongoDB. Use a reachable development MongoDB deployment and allow access only from needed EC2 public or private addresses.

## Create EC2 instance

1. Start AWS Academy lab session.
2. Open AWS Console using lab-provided link and region.
3. Launch one Ubuntu LTS EC2 instance in lab-provided VPC and public subnet.
4. Create or select EC2 key pair when sandbox permits it. Store downloaded `.pem` file outside repository and restrict its permissions:

   ```bash
   chmod 400 /path/to/key.pem
   ```

5. Enable public IPv4 address for this single-host sandbox instance.
6. Record instance public IPv4 address. It can change after stop/start when no Elastic IP is available.

## Security group

Create least-privilege inbound rules.

| Protocol | Port | Source | Purpose |
| --- | ---: | --- | --- |
| TCP | 22 | Your current public IP `/32` | SSH administration |
| TCP | 80 | Your current public IP `/32`, or lab test CIDR | HTTP access through Nginx |

Do not expose Redis or direct service ports publicly. Do not add `0.0.0.0/0` for ports `6379`, `5001`, `5002`, `8000` through `8005`, or MongoDB.

## Prepare Ubuntu

Connect with SSH using public IPv4 address:

```bash
ssh -i /path/to/key.pem ubuntu@EC2_PUBLIC_IP
```

Install Git, Docker Engine, and Docker Compose plugin:

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-v2
sudo usermod -aG docker "$USER"
exit
```

Reconnect, then verify Docker access:

```bash
docker --version
docker compose version
docker ps
```

## Configure application

Clone repository on EC2:

```bash
git clone https://github.com/senghakch17-byte/AMT-MobileApp.git
cd AMT-MobileApp
```

Create service environment files from templates. Use real development values, never placeholders:

```bash
cp apps/registration-service/.env.example apps/registration-service/.env
cp apps/login-service/.env.example apps/login-service/.env
cp apps/attendance-service/.env.example apps/attendance-service/.env
cp apps/request-service/.env.example apps/request-service/.env
cp apps/event-service/.env.example apps/event-service/.env
cp apps/notification-service/.env.example apps/notification-service/.env
cp apps/member-service/.env.example apps/member-service/.env
cp apps/library-service/.env.example apps/library-service/.env
cp apps/api-gateway/.env.example apps/api-gateway/.env
```

Set matching `JWT_SECRET` values for gateway and every service that verifies tokens. Set MongoDB connection values, `INTERNAL_API_KEY`, and service URLs in matching `.env` files. See [configuration guide](CONFIGURATION.md).

Keep environment files on EC2 only:

```bash
chmod 600 apps/*/.env
```

## Start and verify

From repository root:

```bash
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs --tail=200
curl http://localhost/health
```

From development machine:

```bash
curl http://EC2_PUBLIC_IP/health
```

Expected response contains gateway status JSON. Use [Postman collection](postman/README.md) for registration, login, and protected route checks.

## Existing multi-host Compose files

`deploy/ec2-A.compose.yaml` through `deploy/ec2-D.compose.yaml` describe intended split-host topology:

| Host | Intended services |
| --- | --- |
| EC2-A | Nginx, two API gateways, registration, login, Redis |
| EC2-B | Request, event |
| EC2-C | Attendance, notification |
| EC2-D | Member, library |

This topology is configured but not deployed or production-verified. Each host must have repository checkout and identical ignored `deploy/.env`. Use private IPs only for service-to-service traffic. Place EC2 private addresses and shared application settings in `deploy/.env`, based on `deploy/.env.example`.

On each host, create shared deployment environment file and set real values. Deploy Compose passes `deploy/.env` to application containers; Python services receive `MONGODB_URI` from shared `MONGO_URI`, so no per-service `.env` files are needed:

```bash
cp deploy/.env.example deploy/.env
chmod 600 deploy/.env
```

Run commands for matching host. Replace `git pull` with explicit release checkout when deploying a tagged release.

### EC2-A: Nginx, gateways, registration, login, Redis

```bash
cd ~/AMT-MobileApp
git pull
docker compose --env-file deploy/.env -f deploy/ec2-A.compose.yaml config --quiet
docker compose --env-file deploy/.env -f deploy/ec2-A.compose.yaml up -d --build
docker compose --env-file deploy/.env -f deploy/ec2-A.compose.yaml ps
docker compose --env-file deploy/.env -f deploy/ec2-A.compose.yaml logs --tail=200

# Nginx and gateway reachability
curl --fail --show-error http://localhost/health

# Registration and login have no health endpoint. Confirm processes and inspect startup logs.
docker compose --env-file deploy/.env -f deploy/ec2-A.compose.yaml ps register login
docker compose --env-file deploy/.env -f deploy/ec2-A.compose.yaml logs --tail=100 register login

```

### EC2-B: request and event

```bash
cd ~/AMT-MobileApp
git pull
docker compose --env-file deploy/.env -f deploy/ec2-B.compose.yaml config --quiet
docker compose --env-file deploy/.env -f deploy/ec2-B.compose.yaml up -d --build
docker compose --env-file deploy/.env -f deploy/ec2-B.compose.yaml ps
docker compose --env-file deploy/.env -f deploy/ec2-B.compose.yaml logs --tail=200

EC2_B_IP="$(grep '^EC2_B_IP=' deploy/.env | cut -d= -f2-)"

# Request health endpoint.
curl --fail --show-error "http://${EC2_B_IP}:8000/health"

# Event service has no health endpoint. Confirm process and inspect startup logs.
docker compose --env-file deploy/.env -f deploy/ec2-B.compose.yaml ps event-service
docker compose --env-file deploy/.env -f deploy/ec2-B.compose.yaml logs --tail=100 event-service

```

### EC2-C: attendance and notification

```bash
cd ~/AMT-MobileApp
git pull
docker compose --env-file deploy/.env -f deploy/ec2-C.compose.yaml config --quiet
docker compose --env-file deploy/.env -f deploy/ec2-C.compose.yaml up -d --build
docker compose --env-file deploy/.env -f deploy/ec2-C.compose.yaml ps
docker compose --env-file deploy/.env -f deploy/ec2-C.compose.yaml logs --tail=200

EC2_C_IP="$(grep '^EC2_C_IP=' deploy/.env | cut -d= -f2-)"
curl --fail --show-error "http://${EC2_C_IP}:8002/health"
curl --fail --show-error "http://${EC2_C_IP}:8005/health"

```

Notification health returns HTTP `503` until its Redis worker connects to EC2-A Redis. Check security group rule and `REDIS_URL` when this happens.

### EC2-D: library and member

```bash
cd ~/AMT-MobileApp
git pull
docker compose --env-file deploy/.env -f deploy/ec2-D.compose.yaml config --quiet
docker compose --env-file deploy/.env -f deploy/ec2-D.compose.yaml up -d --build
docker compose --env-file deploy/.env -f deploy/ec2-D.compose.yaml ps
docker compose --env-file deploy/.env -f deploy/ec2-D.compose.yaml logs --tail=200

EC2_D_IP="$(grep '^EC2_D_IP=' deploy/.env | cut -d= -f2-)"
curl --fail --show-error "http://${EC2_D_IP}:8003/health"
curl --fail --show-error "http://${EC2_D_IP}:8004/health"

```

EC2-A uses Nginx port `80`; EC2-B, EC2-C, EC2-D service ports and EC2-A Redis bind only to host private IP addresses. Redis has no persistence. `POST /notification/api/v1/internal/events` remains excluded from public gateway use.

Stop only matching host services:

```bash
docker compose --env-file deploy/.env -f deploy/ec2-A.compose.yaml down
docker compose --env-file deploy/.env -f deploy/ec2-B.compose.yaml down
docker compose --env-file deploy/.env -f deploy/ec2-C.compose.yaml down
docker compose --env-file deploy/.env -f deploy/ec2-D.compose.yaml down
```

Multi-host security groups must allow only required private traffic:

| Destination | Port | Allowed source |
| --- | ---: | --- |
| EC2-A Nginx | 80 | Test clients |
| EC2-A Redis | 6379 | EC2-B and EC2-C security groups only |
| EC2-B services | 8000, 8001 | EC2-A gateway only |
| EC2-C Attendance | 8002 | EC2-A gateway only |
| EC2-C Notification | 8005 | EC2-A gateway and EC2-B service group for internal events |
| EC2-D Library | 8003 | EC2-A gateway only |
| EC2-D Member | 8004 | EC2-A gateway only |

SSH access remains restricted to your current public IP. Never publish direct service or Redis ports to internet.

## Stop and clean up

At end of each lab:

```bash
cd ~/AMT-MobileApp
docker compose down
```

In AWS Console, terminate EC2 instance when lab work ends. Also remove unused EBS volumes, snapshots, Elastic IPs, load balancers, NAT gateways, and test security groups if sandbox allows their creation. Stopped instances can still incur EBS charges; NAT gateways and load balancers can consume student credits quickly.

## Production gap

This guide does not provide production deployment. Production needs reviewed multi-host Compose files or orchestration, HTTPS and domain setup, managed secrets, backup and restore procedures, monitoring, alerting, least-privilege IAM, network design, and tested recovery procedures.