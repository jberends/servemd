# Kubernetes Deployment

Deploy servemd to Kubernetes or k3s clusters.

## Prerequisites

- Kubernetes cluster (k3s, k8s, GKE, EKS, AKS, etc.)
- `kubectl` configured
- Docker image pushed to a registry (see [User Dockerfile](./user-dockerfile.md))

## Quick Deployment

### Option 1: Using Your Custom Image

If you've built a custom image with your docs bundled:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docs-server
  labels:
    app: docs-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: docs-server
  template:
    metadata:
      labels:
        app: docs-server
    spec:
      containers:
      - name: docs-server
        image: ghcr.io/mycompany/docs:latest
        ports:
        - containerPort: 8080
        env:
        - name: BASE_URL
          value: "https://docs.mycompany.com"
        - name: DEBUG
          value: "false"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: docs-server
spec:
  selector:
    app: docs-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

Deploy:

```bash
kubectl apply -f deployment.yaml
```

### Option 2: Using Base Image + ConfigMap

If you want to keep docs separate from the image:

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: docs-content
data:
  index.md: |
    # Welcome to Our Documentation
    
    This is served from a ConfigMap!
  
  sidebar.md: |
    # Navigation
    
    - [Home](index.html)
    - [Features](features.html)
  
  topbar.md: |
    # Documentation
    
    [GitHub](https://github.com/mycompany/project)
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docs-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: docs-server
  template:
    metadata:
      labels:
        app: docs-server
    spec:
      containers:
      - name: docs-server
        image: ghcr.io/yourusername/servemd:latest
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: docs-volume
          mountPath: /app/docs
      volumes:
      - name: docs-volume
        configMap:
          name: docs-content
---
apiVersion: v1
kind: Service
metadata:
  name: docs-server
spec:
  selector:
    app: docs-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
```

Deploy:

```bash
kubectl apply -f configmap.yaml
```

### Option 3: Using PersistentVolume

For larger documentation sets stored in persistent storage:

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: docs-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docs-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: docs-server
  template:
    metadata:
      labels:
        app: docs-server
    spec:
      containers:
      - name: docs-server
        image: ghcr.io/yourusername/servemd:latest
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: docs-storage
          mountPath: /app/docs
      volumes:
      - name: docs-storage
        persistentVolumeClaim:
          claimName: docs-pvc
```

## Ingress Configuration

### NGINX Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: docs-ingress
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - docs.mycompany.com
    secretName: docs-tls
  rules:
  - host: docs.mycompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: docs-server
            port:
              number: 80
```

Apply:

```bash
kubectl apply -f ingress.yaml
```

### Traefik Ingress (k3s default)

```yaml
# ingress-traefik.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: docs-ingress
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: websecure
    traefik.ingress.kubernetes.io/router.tls: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  rules:
  - host: docs.mycompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: docs-server
            port:
              number: 80
  tls:
  - hosts:
    - docs.mycompany.com
    secretName: docs-tls
```

## Complete k3s Example

Perfect for edge computing and home labs:

```bash
# 1. Install k3s (if not already installed)
curl -sfL https://get.k3s.io | sh -

# 2. Save this as docs-k3s.yaml
cat <<EOF > docs-k3s.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docs-server
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: docs-server
  template:
    metadata:
      labels:
        app: docs-server
    spec:
      containers:
      - name: docs-server
        image: ghcr.io/mycompany/docs:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
        env:
        - name: BASE_URL
          value: "https://docs.mycompany.com"
---
apiVersion: v1
kind: Service
metadata:
  name: docs-server
  namespace: default
spec:
  selector:
    app: docs-server
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: docs-ingress
  namespace: default
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web
spec:
  rules:
  - host: docs.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: docs-server
            port:
              number: 80
EOF

# 3. Deploy
kubectl apply -f docs-k3s.yaml

# 4. Add to /etc/hosts for local testing
echo "127.0.0.1 docs.local" | sudo tee -a /etc/hosts

# 5. Visit http://docs.local
```

## Helm Chart

Create a reusable Helm chart:

```yaml
# Chart.yaml
apiVersion: v2
name: servemd-docs
description: Helm chart for ServeM documentation server
type: application
version: 1.0.0
appVersion: "1.0.0"
```

```yaml
# values.yaml
replicaCount: 2

image:
  repository: ghcr.io/mycompany/docs
  tag: latest
  pullPolicy: Always

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: docs.mycompany.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: docs-tls
      hosts:
        - docs.mycompany.com

env:
  BASE_URL: "https://docs.mycompany.com"
  DEBUG: "false"

resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

Install:

```bash
helm install my-docs ./servemd-docs
```

## GitOps with ArgoCD

```yaml
# argocd-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: docs-server
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/mycompany/docs
    targetRevision: HEAD
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## CI/CD Integration

### GitHub Actions + kubectl

```yaml
# .github/workflows/deploy-k8s.yml
name: Deploy to Kubernetes

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build and push Docker image
        run: |
          docker build -t ghcr.io/${{ github.repository }}/docs:${{ github.sha }} .
          echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker push ghcr.io/${{ github.repository }}/docs:${{ github.sha }}
      
      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
        
      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBECONFIG }}" | base64 -d > kubeconfig.yaml
          export KUBECONFIG=kubeconfig.yaml
          
      - name: Deploy to k8s
        run: |
          kubectl set image deployment/docs-server docs-server=ghcr.io/${{ github.repository }}/docs:${{ github.sha }}
          kubectl rollout status deployment/docs-server
```

## Monitoring

### Prometheus Metrics (Future)

The server includes a `/health` endpoint. You can extend it to expose Prometheus metrics:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: docs-server
  labels:
    app: docs-server
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/health"
spec:
  selector:
    app: docs-server
  ports:
  - port: 80
    targetPort: 8080
```

## Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: docs-server-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: docs-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Next Steps

- **[Cloud Platforms](./cloud-platforms.md)** - Deploy to managed services
- **[User Dockerfile](./user-dockerfile.md)** - Build custom images
- **[Configuration](../configuration.md)** - Environment variables
