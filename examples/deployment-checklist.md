# MCP Deployment Checklist

This checklist helps ensure a smooth deployment of ServeMD with MCP support.

## Pre-Deployment

### 1. Local Testing

- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check src/ tests/`
- [ ] Code formatted: `uv run ruff format src/ tests/`
- [ ] Build MCP index: `uv run python -m docs_server.mcp.cli build`
- [ ] Validate cache: `uv run python -m docs_server.mcp.cli validate`
- [ ] Check index info: `uv run python -m docs_server.mcp.cli info`

### 2. Docker Build

- [ ] Docker builds successfully: `docker build -t servemd .`
- [ ] Test container locally:
  ```bash
  docker run -p 8080:8080 \
    -v $(pwd)/docs:/app/docs \
    -e MCP_ENABLED=true \
    servemd
  ```
- [ ] Verify startup time (<2 seconds)
- [ ] Check cache creation: `docker exec <container> ls /app/cache/mcp/`

### 3. API Testing

Test all endpoints with curl:

```bash
# Health check
curl http://localhost:8080/health

# MCP Initialize
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}}}'

# MCP Tools List
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"2","method":"tools/list"}'

# MCP Search
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"3","method":"tools/call","params":{"name":"search_docs","arguments":{"query":"configuration"}}}'
```

- [ ] `/health` returns 200 with `mcp_enabled: true`
- [ ] `initialize` returns server info
- [ ] `tools/list` returns 3 tools
- [ ] `search_docs` returns results

### 4. Rate Limiting

- [ ] Test rate limit enforcement:
  ```bash
  for i in {1..125}; do
    curl -X POST http://localhost:8080/mcp \
      -H "Content-Type: application/json" \
      -d '{"jsonrpc":"2.0","id":"'$i'","method":"tools/list"}' &
  done
  wait
  ```
- [ ] Verify 429 response after limit exceeded
- [ ] Check error includes `retryAfter` and `limit`

## Deployment

### 5. Environment Configuration

Verify environment variables:

```bash
# Required
DOCS_ROOT=/app/docs
CACHE_ROOT=/app/cache

# Optional (with defaults)
MCP_ENABLED=true
MCP_RATE_LIMIT_REQUESTS=120
MCP_RATE_LIMIT_WINDOW=60
MCP_MAX_SEARCH_RESULTS=10
MCP_SNIPPET_LENGTH=200
DEBUG=false
```

### 6. Kubernetes Deployment

If deploying to k8s/k3s:

- [ ] Configure emptyDir volume for cache:
  ```yaml
  volumes:
    - name: cache
      emptyDir: {}
  volumeMounts:
    - name: cache
      mountPath: /app/cache
  ```
- [ ] Set resource limits (recommended: 256Mi memory)
- [ ] Configure liveness probe: `GET /health`
- [ ] Configure readiness probe: `GET /health`
- [ ] Set `imagePullPolicy: Always` for updates

### 7. Deploy

- [ ] Backup existing deployment (if applicable)
- [ ] Deploy new version:
  ```bash
  kubectl apply -f k8s-manifest.yaml
  ```
- [ ] Wait for rollout:
  ```bash
  kubectl rollout status deployment/servemd
  ```
- [ ] Check pod logs:
  ```bash
  kubectl logs -l app=servemd --tail=50
  ```

## Post-Deployment

### 8. Verification

- [ ] Health check passes: `curl https://docs.example.com/health`
- [ ] Existing endpoints work:
  - [ ] `GET /` redirects to `/index.html`
  - [ ] `GET /index.html` returns HTML
  - [ ] `GET /llms.txt` returns text
  - [ ] `GET /llms-full.txt` returns text
- [ ] MCP endpoint works:
  - [ ] Initialize handshake succeeds
  - [ ] Tools list returns 3 tools
  - [ ] Search returns results

### 9. Log Monitoring

Check logs for MCP activity:

```bash
# Kubernetes
kubectl logs -l app=servemd --tail=100 | grep "\[MCP\]"

# Docker
docker logs <container> | grep "\[MCP\]"
```

Expected log entries:
```
[MCP] index built: 14 docs (184.4ms)
[MCP] method=initialize id=1
[MCP] method=tools/call tool=search_docs
[MCP] search query="config" results=3
```

- [ ] No errors in logs
- [ ] Index loaded/built successfully
- [ ] MCP requests being served

### 10. Performance Monitoring

Monitor for first 24 hours:

- [ ] Response times (<100ms for search)
- [ ] Memory usage (stable, <256Mi)
- [ ] CPU usage (normal, <0.1 cores)
- [ ] Rate limit hits (check if too restrictive)
- [ ] Error rates (<1%)

### 11. Cache Persistence

Test cache persistence:

```bash
# Scale down
kubectl scale deployment/servemd --replicas=0

# Scale up
kubectl scale deployment/servemd --replicas=1

# Check logs
kubectl logs -l app=servemd --tail=50 | grep "index loaded from cache"
```

- [ ] Index loads from cache on restart (~10ms)
- [ ] No full rebuild unless docs changed

## Rollback Plan

If issues arise:

### Option 1: Disable MCP

```bash
# Set environment variable
kubectl set env deployment/servemd MCP_ENABLED=false
```

### Option 2: Scale Down

```bash
kubectl scale deployment/servemd --replicas=0
```

### Option 3: Full Rollback

```bash
kubectl rollout undo deployment/servemd
```

## Troubleshooting

### Index Not Building

```bash
# Get pod shell
kubectl exec -it <pod> -- /bin/sh

# Check docs directory
ls -la /app/docs/

# Manually build index
python -m docs_server.mcp.cli build

# Check logs
python -m docs_server.mcp.cli info
```

### Rate Limit Too Restrictive

Increase limits:

```yaml
env:
  - name: MCP_RATE_LIMIT_REQUESTS
    value: "300"  # Increase from 120
```

### Cache Not Persisting

Verify volume mount:

```bash
kubectl exec -it <pod> -- ls -la /app/cache/mcp/
```

## Success Metrics

After 24 hours, verify:

- [ ] Uptime: 99.9%+
- [ ] Error rate: <1%
- [ ] Average response time: <100ms
- [ ] No memory leaks (stable memory usage)
- [ ] No rate limit complaints (or adjust limits)
- [ ] Positive user feedback

## Notes

- MCP is optional - existing functionality unaffected if disabled
- Each pod has independent cache (no shared state required)
- Rate limits are per-pod (scale pods to increase throughput)
- Index rebuilds automatically when docs change
- Health check passes before MCP initialization (non-blocking)
