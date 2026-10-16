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
git clone REPOSITORY_URL AMT-MobileApp
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

Do not use this topology for a sandbox lab yet. It remains incomplete and unverified:

- EC2-A build and `env_file` paths do not match active repository layout.
- Notification service on EC2-C needs remote Redis configuration for EC2-A.
- Redis has no persistence and its published port needs security-group restrictions.
- Gateway currently proxies notification internal ingestion route; that route must remain private to service callers.
- EC2-D references member and library services not present in active application service map.
- Each host requires its own service `.env` files and private-IP configuration.

When these gaps are fixed, use private IPs only for service-to-service traffic. Place EC2 private addresses in ignored `deploy/.env`, based on `deploy/.env.example`.

Multi-host security groups must allow only required private traffic:

| Destination | Port | Allowed source |
| --- | ---: | --- |
| EC2-A Nginx | 80 | Test clients |
| EC2-A Redis | 6379 | EC2-B and EC2-C security groups only |
| EC2-B services | 8000, 8001 | EC2-A gateway only |
| EC2-C services | 8004, 8005 | EC2-A gateway; EC2-B may access `8005` for internal events |

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