# Cloud Platform Deployment

Deploy servemd to popular cloud platforms and hosting services.

## Heroku

### Method 1: Container Registry (Recommended)

```bash
# 1. Create Heroku app
heroku create my-docs-server

# 2. Login to Heroku Container Registry
heroku container:login

# 3. Build and push
heroku container:push web -a my-docs-server

# 4. Release
heroku container:release web -a my-docs-server

# 5. Set environment variables
heroku config:set BASE_URL=https://my-docs-server.herokuapp.com -a my-docs-server

# 6. Open
heroku open -a my-docs-server
```

### Method 2: With heroku.yml

Create `heroku.yml` in your docs repository:

```yaml
build:
  docker:
    web: Dockerfile
run:
  web: python -m docs_server
```

Create `Dockerfile`:

```dockerfile
FROM ghcr.io/yourusername/servemd:latest
COPY . /app/docs/
ENV BASE_URL=$BASE_URL
```

Deploy:

```bash
heroku stack:set container -a my-docs-server
git push heroku main
```

### Auto-deploy with GitHub

```bash
# Connect to GitHub
heroku git:remote -a my-docs-server

# Enable auto-deploy
# Go to: https://dashboard.heroku.com/apps/my-docs-server/deploy/github
# Connect repo and enable automatic deploys from main branch
```

## Railway.app

Railway is modern, fast, and developer-friendly.

### Quick Deploy

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Link to your docs
railway link

# 5. Deploy
railway up

# 6. Set custom domain (optional)
railway domain
```

### Using railway.json

Create `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "dockerfile",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "python -m docs_server",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "on-failure",
    "restartPolicyMaxRetries": 10
  }
}
```

### GitHub Integration

1. Visit [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your docs repository
4. Railway auto-detects Dockerfile and deploys
5. Set environment variables in dashboard:
   - `BASE_URL=https://your-docs.up.railway.app`

## Fly.io

Fly.io is excellent for edge deployment with global distribution.

### Setup

```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh

# 2. Login
flyctl auth login

# 3. Launch app (creates fly.toml)
flyctl launch
```

This creates `fly.toml`:

```toml
app = "my-docs"
primary_region = "iad"

[build]
  image = "ghcr.io/mycompany/docs:latest"

[env]
  BASE_URL = "https://my-docs.fly.dev"
  DEBUG = "false"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

Deploy:

```bash
# Deploy
flyctl deploy

# Open
flyctl open

# View logs
flyctl logs
```

### Multi-region Deployment

```bash
# Add regions for global distribution
flyctl regions add iad ord lhr syd

# Scale to multiple regions
flyctl scale count 3

# Check status
flyctl status
```

## DigitalOcean App Platform

### Using Container Registry

```bash
# 1. Push to DO Container Registry
doctl registry login
docker tag my-docs registry.digitalocean.com/myregistry/docs:latest
docker push registry.digitalocean.com/myregistry/docs:latest

# 2. Create app via doctl
doctl apps create --spec app-spec.yaml
```

Create `app-spec.yaml`:

```yaml
name: docs-server
services:
- name: web
  image:
    registry_type: DOCR
    repository: docs
    tag: latest
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8080
  health_check:
    http_path: /health
  envs:
  - key: BASE_URL
    value: https://docs-server.ondigitalocean.app
  - key: DEBUG
    value: "false"
```

### Using GitHub Integration

1. Visit [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Click "Create App" → "GitHub"
3. Select repository
4. Configure:
   - Type: Docker Hub / Registry
   - Image: `ghcr.io/mycompany/docs:latest`
   - HTTP Port: 8080
   - Health Check: `/health`
5. Deploy

## Render.com

Simple and affordable for documentation hosting.

### Using render.yaml

Create `render.yaml`:

```yaml
services:
  - type: web
    name: docs-server
    runtime: image
    image:
      url: ghcr.io/mycompany/docs:latest
    plan: starter
    healthCheckPath: /health
    envVars:
      - key: BASE_URL
        value: https://docs-server.onrender.com
      - key: DEBUG
        value: false
```

### Manual Deployment

1. Visit [render.com](https://render.com)
2. Click "New" → "Web Service"
3. Connect repository
4. Configure:
   - Environment: Docker
   - Dockerfile path: `./Dockerfile`
   - Instance type: Starter
5. Add environment variable:
   - `BASE_URL=https://your-app.onrender.com`
6. Deploy

## Google Cloud Run

Serverless container deployment that scales to zero.

```bash
# 1. Push image to GCR
gcloud auth configure-docker
docker tag my-docs gcr.io/PROJECT_ID/docs:latest
docker push gcr.io/PROJECT_ID/docs:latest

# 2. Deploy to Cloud Run
gcloud run deploy docs-server \
  --image gcr.io/PROJECT_ID/docs:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="BASE_URL=https://docs-server-xxx.run.app"

# 3. Get URL
gcloud run services describe docs-server --region us-central1 --format 'value(status.url)'
```

### With Custom Domain

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service docs-server \
  --domain docs.mycompany.com \
  --region us-central1
```

## AWS (ECS Fargate)

### Using AWS CLI

```bash
# 1. Push to ECR
aws ecr create-repository --repository-name docs-server
aws ecr get-login-password | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com
docker tag my-docs ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/docs-server:latest
docker push ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/docs-server:latest

# 2. Create ECS task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 3. Create service
aws ecs create-service \
  --cluster default \
  --service-name docs-server \
  --task-definition docs-server \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

Create `task-definition.json`:

```json
{
  "family": "docs-server",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "docs-server",
      "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/docs-server:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "BASE_URL",
          "value": "https://docs.mycompany.com"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

## Azure Container Instances

```bash
# 1. Push to ACR
az acr create --resource-group myResourceGroup --name myregistry --sku Basic
az acr login --name myregistry
docker tag my-docs myregistry.azurecr.io/docs-server:latest
docker push myregistry.azurecr.io/docs-server:latest

# 2. Deploy to ACI
az container create \
  --resource-group myResourceGroup \
  --name docs-server \
  --image myregistry.azurecr.io/docs-server:latest \
  --registry-login-server myregistry.azurecr.io \
  --registry-username $(az acr credential show --name myregistry --query username -o tsv) \
  --registry-password $(az acr credential show --name myregistry --query passwords[0].value -o tsv) \
  --dns-name-label my-docs \
  --ports 8080 \
  --environment-variables BASE_URL=https://my-docs.region.azurecontainer.io:8080

# 3. Get URL
az container show --resource-group myResourceGroup --name docs-server --query ipAddress.fqdn
```

## Comparison

| Platform | Pricing | Ease | Auto-scaling | Best For |
|----------|---------|------|--------------|----------|
| **Heroku** | $7/mo | ⭐⭐⭐⭐⭐ | ✅ | Simple deploys |
| **Railway** | $5/mo | ⭐⭐⭐⭐⭐ | ✅ | Modern workflow |
| **Fly.io** | Pay-as-go | ⭐⭐⭐⭐ | ✅ | Global edge |
| **DigitalOcean** | $5/mo | ⭐⭐⭐⭐ | ✅ | Predictable pricing |
| **Render** | $7/mo | ⭐⭐⭐⭐⭐ | ✅ | Free tier |
| **Cloud Run** | Pay-as-go | ⭐⭐⭐ | ✅✅ | Serverless |
| **ECS Fargate** | Pay-as-go | ⭐⭐ | ✅ | AWS ecosystem |
| **Azure ACI** | Pay-as-go | ⭐⭐ | ❌ | Azure ecosystem |

## Cost Optimization

### Free Tiers

- **Render**: Free tier with 750 hours/month
- **Fly.io**: 3 shared VMs free
- **Railway**: $5 free credit/month

### Serverless Options

Use Cloud Run or AWS App Runner for documentation that's accessed infrequently:

- Scale to zero when not in use
- Pay only for actual requests
- Cold start: ~1-2 seconds (acceptable for docs)

## CI/CD Examples

### Deploy to Railway (GitHub Actions)

```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Railway CLI
        run: npm install -g @railway/cli
      
      - name: Deploy to Railway
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### Deploy to Fly.io (GitHub Actions)

```yaml
name: Deploy to Fly.io

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: superfly/flyctl-actions/setup-flyctl@master
      
      - name: Deploy to Fly.io
        run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

## Next Steps

- **[Kubernetes Deployment](./kubernetes.md)** - Self-hosted k8s/k3s
- **[User Dockerfile](./user-dockerfile.md)** - Build custom images
- **[Configuration](../configuration.md)** - Environment variables
