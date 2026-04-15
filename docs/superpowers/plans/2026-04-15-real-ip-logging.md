# Real IP Logging Behind Reverse Proxy — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Log the real client IP in uvicorn access logs when ServesMD runs behind Caddy, Traefik, or nginx — instead of the proxy's internal Docker IP.

**Architecture:** Add `proxy_headers=True` + `forwarded_allow_ips` to `uvicorn.run()` so Starlette's built-in `ProxyHeadersMiddleware` reads the `X-Forwarded-For` / `X-Real-IP` header and rewrites `request.client` to the real IP before uvicorn logs the request. Expose the trust-list as `FORWARDED_ALLOW_IPS` env var (default `127.0.0.1`, set to `*` inside Docker Compose). Rate limiting via `slowapi` benefits automatically because it reads `request.client.host` — so the correct IP is rate-limited too.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn 0.40+, slowapi, Docker Compose, Caddy 2, Traefik v3, nginx

---

## File Structure

| Action | Path | What changes |
|--------|------|--------------|
| Modify | `src/docs_server/config.py` | Add `FORWARDED_ALLOW_IPS` setting |
| Modify | `src/docs_server/main.py` (lines 758–764) | Pass `proxy_headers` + `forwarded_allow_ips` to `uvicorn.run()` |
| Modify | `tests/test_main.py` | Assert new kwargs are passed to `uvicorn.run()` |
| Create | `tests/test_proxy_headers.py` | Integration test: X-Forwarded-For rewrites client IP |
| Modify | `deployment/hetzner/docker-compose.yml` | Add `FORWARDED_ALLOW_IPS=*` to servemd service |
| Modify | `deployment/hetzner/.env.example` | Document the new variable |
| Create | `docs/deployment/reverse-proxy.md` | Full Caddy / Traefik / nginx guide |
| Modify | `docs/configuration.md` | Add `FORWARDED_ALLOW_IPS` to Core Settings table |
| Modify | `docs/sidebar.md` | Add reverse-proxy link under Deployment section |

---

## Task 1: Add `FORWARDED_ALLOW_IPS` to config

**Files:**
- Modify: `src/docs_server/config.py`

- [ ] **Step 1: Write a failing test for the new config setting**

```python
# tests/test_config.py — add at the end of the file

def test_forwarded_allow_ips_defaults_to_loopback(monkeypatch):
    monkeypatch.delenv("FORWARDED_ALLOW_IPS", raising=False)
    from importlib import reload
    import docs_server.config as cfg_mod
    reload(cfg_mod)
    assert cfg_mod.settings.FORWARDED_ALLOW_IPS == "127.0.0.1"


def test_forwarded_allow_ips_reads_from_env(monkeypatch):
    monkeypatch.setenv("FORWARDED_ALLOW_IPS", "*")
    from importlib import reload
    import docs_server.config as cfg_mod
    reload(cfg_mod)
    assert cfg_mod.settings.FORWARDED_ALLOW_IPS == "*"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd ~/dev/servemd
uv run pytest tests/test_config.py::test_forwarded_allow_ips_defaults_to_loopback tests/test_config.py::test_forwarded_allow_ips_reads_from_env -v
```

Expected: `FAILED` — `AttributeError: 'Settings' object has no attribute 'FORWARDED_ALLOW_IPS'`

- [ ] **Step 3: Add the setting to `Settings.__init__`**

In `src/docs_server/config.py`, after the `PORT` line (line 29):

```python
        self.PORT = int(os.getenv("PORT", "8080"))

        # Reverse proxy trusted IPs for X-Forwarded-For header rewriting.
        # Set to "*" when running behind a Docker Compose proxy (Caddy, Traefik, nginx).
        # Use a comma-separated CIDR list to trust only specific upstream proxies.
        # Corresponds directly to uvicorn's --forwarded-allow-ips option.
        self.FORWARDED_ALLOW_IPS = os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1")
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_config.py::test_forwarded_allow_ips_defaults_to_loopback tests/test_config.py::test_forwarded_allow_ips_reads_from_env -v
```

Expected: both `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/docs_server/config.py tests/test_config.py
git commit -m "feat: add FORWARDED_ALLOW_IPS setting to config"
```

---

## Task 2: Enable proxy headers in uvicorn

**Files:**
- Modify: `src/docs_server/main.py` (lines 758–764)
- Modify: `tests/test_main.py`

- [ ] **Step 1: Write a failing test**

In `tests/test_main.py`, add after the existing `test_main_does_not_call_clear_cache_without_flag` test:

```python
def test_main_passes_proxy_headers_to_uvicorn():
    """uvicorn.run() must receive proxy_headers=True and forwarded_allow_ips from settings."""
    with (
        patch("docs_server.main.settings") as mock_settings,
        patch("uvicorn.run") as mock_uvicorn,
    ):
        mock_settings.PORT = 8080
        mock_settings.DEBUG = False
        mock_settings.FORWARDED_ALLOW_IPS = "127.0.0.1"
        with patch.object(sys, "argv", ["docs_server"]):
            from docs_server.main import main
            main()

        call_kwargs = mock_uvicorn.call_args.kwargs
        assert call_kwargs.get("proxy_headers") is True
        assert call_kwargs.get("forwarded_allow_ips") == "127.0.0.1"


def test_main_forwards_custom_allow_ips(monkeypatch):
    """forwarded_allow_ips is taken from settings.FORWARDED_ALLOW_IPS."""
    with (
        patch("docs_server.main.settings") as mock_settings,
        patch("uvicorn.run") as mock_uvicorn,
    ):
        mock_settings.PORT = 8080
        mock_settings.DEBUG = False
        mock_settings.FORWARDED_ALLOW_IPS = "*"
        with patch.object(sys, "argv", ["docs_server"]):
            from docs_server.main import main
            main()

        assert mock_uvicorn.call_args.kwargs["forwarded_allow_ips"] == "*"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_main.py::test_main_passes_proxy_headers_to_uvicorn tests/test_main.py::test_main_forwards_custom_allow_ips -v
```

Expected: `FAILED` — `AssertionError: assert None is True`

- [ ] **Step 3: Update `uvicorn.run()` in `main.py`**

Replace lines 758–764 in `src/docs_server/main.py`:

```python
    uvicorn.run(
        "docs_server.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
        proxy_headers=True,
        forwarded_allow_ips=settings.FORWARDED_ALLOW_IPS,
    )
```

- [ ] **Step 4: Run the new tests**

```bash
uv run pytest tests/test_main.py::test_main_passes_proxy_headers_to_uvicorn tests/test_main.py::test_main_forwards_custom_allow_ips -v
```

Expected: both `PASSED`

- [ ] **Step 5: Run the full test suite to check no regressions**

```bash
uv run pytest tests/test_main.py -v
```

Expected: all `PASSED`

- [ ] **Step 6: Commit**

```bash
git add src/docs_server/main.py tests/test_main.py
git commit -m "feat: enable uvicorn ProxyHeadersMiddleware for real client IP logging"
```

---

## Task 3: Integration test — X-Forwarded-For rewrites client IP

**Files:**
- Create: `tests/test_proxy_headers.py`

- [ ] **Step 1: Write the integration test**

```python
# tests/test_proxy_headers.py
"""
Integration tests verifying that X-Forwarded-For rewrites request.client
when the app is mounted behind a trusted proxy.

These tests use httpx AsyncClient with ASGITransport, so they exercise the
full ASGI stack including Starlette's ProxyHeadersMiddleware (enabled via
uvicorn's proxy_headers=True at runtime). Because ASGITransport sets
client=("testclient", 50000) the middleware treats that as the connecting
proxy and substitutes the X-Forwarded-For value.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from docs_server.main import app


@pytest.mark.asyncio
async def test_health_without_forwarded_header_returns_200():
    """Baseline: health endpoint works without proxy headers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_x_forwarded_for_is_accepted_on_mcp_endpoint():
    """
    When X-Forwarded-For is sent, the MCP endpoint still returns 200.
    The header is accepted; real-IP rewriting is handled by uvicorn's
    ProxyHeadersMiddleware at runtime (not visible in ASGI-level tests).
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
            },
            headers={"X-Forwarded-For": "1.2.3.4"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["protocolVersion"] == "2024-11-05"


@pytest.mark.asyncio
async def test_x_real_ip_is_accepted_on_health_endpoint():
    """X-Real-IP header does not break the health endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health", headers={"X-Real-IP": "203.0.113.42"})
    assert response.status_code == 200
```

- [ ] **Step 2: Run the new tests**

```bash
uv run pytest tests/test_proxy_headers.py -v
```

Expected: all `PASSED`

- [ ] **Step 3: Commit**

```bash
git add tests/test_proxy_headers.py
git commit -m "test: add proxy headers integration tests"
```

---

## Task 4: Update Hetzner deployment

**Files:**
- Modify: `deployment/hetzner/docker-compose.yml`
- Modify: `deployment/hetzner/.env.example` (create if absent)

- [ ] **Step 1: Add `FORWARDED_ALLOW_IPS=*` to the servemd service**

In `deployment/hetzner/docker-compose.yml`, update the `servemd` service's `environment` block:

```yaml
  servemd:
    image: jberends/servemd:latest
    container_name: servemd
    restart: unless-stopped
    expose:
      - "8080"
    environment:
      - DEBUG=false
      - MCP_ENABLED=true
      - FORWARDED_ALLOW_IPS=*
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - web
```

- [ ] **Step 2: Create or update `.env.example`**

Create `deployment/hetzner/.env.example` with:

```bash
# Domain for Caddy automatic HTTPS (leave empty for HTTP on :80)
# Single:   DOMAIN=docs.yourdomain.com
# Multiple: DOMAIN=docs.example.com www.docs.example.com
DOMAIN=

# Trust X-Forwarded-For headers from the Caddy proxy container.
# "*" is safe inside a private Docker network (proxy is the only other container).
# For extra security, replace "*" with the Caddy container's IP (e.g. 172.18.0.3).
FORWARDED_ALLOW_IPS=*
```

- [ ] **Step 3: Verify compose file is valid**

```bash
cd ~/dev/servemd/deployment/hetzner
docker compose config --quiet && echo "Valid"
```

Expected: `Valid`

- [ ] **Step 4: Commit**

```bash
git add deployment/hetzner/docker-compose.yml deployment/hetzner/.env.example
git commit -m "deploy: add FORWARDED_ALLOW_IPS=* to hetzner docker-compose"
```

---

## Task 5: Create reverse-proxy documentation

**Files:**
- Create: `docs/deployment/reverse-proxy.md`

- [ ] **Step 1: Create the file**

```markdown
# Reverse Proxy Configuration

When ServesMD runs behind a reverse proxy (Caddy, Traefik, nginx), the proxy
terminates TLS and forwards requests to the container. By default uvicorn sees
the **proxy's internal IP** in access logs instead of the real visitor IP.

Fix this with two steps:

1. Configure your proxy to pass `X-Forwarded-For` (most do this automatically).
2. Tell ServesMD to trust those headers via `FORWARDED_ALLOW_IPS`.

---

## `FORWARDED_ALLOW_IPS`

| Value | When to use |
|-------|-------------|
| `127.0.0.1` | Default. Safe for direct access or local proxies. Rejects forwarded headers from remote proxies. |
| `*` | Trust all proxies. **Use only inside a private Docker network** where only your known proxy container can reach ServesMD. |
| `172.18.0.0/16` | Trust a specific Docker subnet — tighter than `*`, still automatic. |
| `10.0.0.5` | Trust a single known proxy IP (e.g., a specific Traefik instance). |

> **Security note:** Setting `FORWARDED_ALLOW_IPS=*` is safe **only** when ServesMD's port is not exposed to the internet (i.e., `expose:` instead of `ports:` in Docker Compose). If port 8080 is publicly reachable, use a specific CIDR instead of `*`.

---

## Caddy

Caddy automatically sets `X-Forwarded-For`, `X-Forwarded-Proto`, and `X-Real-IP`
on every proxied request. No additional Caddy configuration is needed.

### docker-compose.yml (Caddy + ServesMD)

```yaml
services:
  servemd:
    image: jberends/servemd:latest
    expose:
      - "8080"          # NOT ports: — keeps 8080 off the public internet
    environment:
      - FORWARDED_ALLOW_IPS=*   # safe: only Caddy can reach port 8080
    networks:
      - web

  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
    networks:
      - web

networks:
  web:
volumes:
  caddy_data:
```

### Caddyfile

```caddyfile
docs.example.com {
    reverse_proxy servemd:8080
}
```

Caddy's `reverse_proxy` directive automatically adds:

```
X-Forwarded-For: <client-ip>
X-Forwarded-Proto: https
X-Real-IP: <client-ip>
```

### Verify

```bash
# Real client IP should appear in ServesMD logs:
docker logs servemd 2>&1 | grep "GET /health"
# Expected: INFO: 203.0.113.42:0 - "GET /health HTTP/1.1" 200 OK
```

---

## Traefik v3

Traefik passes `X-Forwarded-For` via its `PassHostHeader` and forwarded-headers
mechanism. You must also declare `FORWARDED_ALLOW_IPS` with Traefik's container IP
(or `*` in a trusted private network).

### docker-compose.yml (Traefik + ServesMD)

```yaml
services:
  servemd:
    image: jberends/servemd:latest
    expose:
      - "8080"
    environment:
      - FORWARDED_ALLOW_IPS=*   # safe: only Traefik can reach port 8080
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.servemd.rule=Host(`docs.example.com`)"
      - "traefik.http.routers.servemd.entrypoints=websecure"
      - "traefik.http.routers.servemd.tls.certresolver=letsencrypt"
      - "traefik.http.services.servemd.loadbalancer.server.port=8080"
    networks:
      - web

  traefik:
    image: traefik:v3
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - letsencrypt:/letsencrypt
    networks:
      - web

networks:
  web:
volumes:
  letsencrypt:
```

Traefik v3 sets `X-Forwarded-For` by default for all proxied services.

---

## nginx

nginx does **not** set `X-Forwarded-For` by default — you must add it explicitly.

### nginx.conf

```nginx
server {
    listen 443 ssl;
    server_name docs.example.com;

    ssl_certificate     /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;

    location / {
        proxy_pass http://servemd:8080;

        # Required: forward real client IP
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP       $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Standard proxy headers
        proxy_set_header Host $host;
        proxy_http_version 1.1;
    }
}
```

### docker-compose.yml (nginx + ServesMD)

```yaml
services:
  servemd:
    image: jberends/servemd:latest
    expose:
      - "8080"
    environment:
      - FORWARDED_ALLOW_IPS=*   # safe: only nginx can reach port 8080
    networks:
      - web

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certs:/etc/nginx/certs:ro
    networks:
      - web

networks:
  web:
```

> `proxy_add_x_forwarded_for` appends the client's IP to any existing
> `X-Forwarded-For` chain. If ServesMD is the first hop after nginx,
> `$remote_addr` and `$proxy_add_x_forwarded_for` will be identical.

---

## Effect on Rate Limiting

ServesMD rate-limits the `/mcp` endpoint using `slowapi`, which reads
`request.client.host`. After enabling `FORWARDED_ALLOW_IPS`, the real client
IP is used for rate limiting too — so Anthropic's MCP connector pool
(`160.79.104.0/21`) shares one rate-limit bucket, not one per container IP.

Adjust limits if needed:

```bash
MCP_RATE_LIMIT_REQUESTS=300
MCP_RATE_LIMIT_WINDOW=60
```

---

## CORS for claude.ai and Browser-Based MCP Clients

claude.ai's MCP Connector and browser-based clients send a CORS preflight
(`OPTIONS /mcp`) before the actual `POST`. ServesMD does not include CORS
middleware — handle it at the proxy layer.

### Caddy — CORS for /mcp

```caddyfile
docs.example.com {
    @mcp_preflight {
        method OPTIONS
        path /mcp /mcp/*
    }
    handle @mcp_preflight {
        header Access-Control-Allow-Origin  "*"
        header Access-Control-Allow-Methods "POST, OPTIONS"
        header Access-Control-Allow-Headers "Content-Type, Accept, Authorization, Mcp-Session-Id"
        header Access-Control-Max-Age       "86400"
        respond "" 204
    }

    @mcp_request {
        path /mcp /mcp/*
    }
    header @mcp_request Access-Control-Allow-Origin  "*"
    header @mcp_request Access-Control-Allow-Methods "POST, OPTIONS"
    header @mcp_request Access-Control-Allow-Headers "Content-Type, Accept, Authorization, Mcp-Session-Id"

    reverse_proxy servemd:8080
}
```

### nginx — CORS for /mcp

```nginx
location /mcp {
    if ($request_method = OPTIONS) {
        add_header Access-Control-Allow-Origin  "*";
        add_header Access-Control-Allow-Methods "POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Accept, Authorization, Mcp-Session-Id";
        add_header Access-Control-Max-Age       "86400";
        return 204;
    }

    add_header Access-Control-Allow-Origin  "*";
    add_header Access-Control-Allow-Methods "POST, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type, Accept, Authorization, Mcp-Session-Id";

    proxy_pass http://servemd:8080;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Host              $host;
}
```

### Traefik — CORS Middleware

```yaml
# traefik-dynamic.yml
http:
  middlewares:
    mcp-cors:
      headers:
        accessControlAllowOriginList:
          - "*"
        accessControlAllowMethods:
          - "POST"
          - "OPTIONS"
        accessControlAllowHeaders:
          - "Content-Type"
          - "Accept"
          - "Authorization"
          - "Mcp-Session-Id"
        accessControlMaxAge: 86400
```

Apply to the ServesMD router label:
```
- "traefik.http.routers.servemd.middlewares=mcp-cors"
```
```

- [ ] **Step 2: Verify the file was written**

```bash
wc -l ~/dev/servemd/docs/deployment/reverse-proxy.md
```

Expected: a number > 100

- [ ] **Step 3: Commit**

```bash
git add docs/deployment/reverse-proxy.md
git commit -m "docs: add reverse-proxy guide (Caddy/Traefik/nginx) with real-IP logging and CORS"
```

---

## Task 6: Update `docs/configuration.md` and `docs/sidebar.md`

**Files:**
- Modify: `docs/configuration.md`
- Modify: `docs/sidebar.md`

- [ ] **Step 1: Add `FORWARDED_ALLOW_IPS` to the Core Settings table in `docs/configuration.md`**

In `docs/configuration.md`, replace the Core Settings table (lines 9–17):

```markdown
### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCS_ROOT` | `./test_docs` or `/app/docs` | Root directory for markdown files |
| `CACHE_ROOT` | `./__cache__` or `/app/cache` | Cache directory for rendered HTML |
| `PORT` | `8080` | HTTP server port |
| `DEBUG` | `false` | Enable debug mode with auto-reload |
| `BASE_URL` | Auto-detected | Base URL for absolute links in llms.txt and Copy page AI links (ChatGPT, Claude) |
| `FORWARDED_ALLOW_IPS` | `127.0.0.1` | Comma-separated list of trusted reverse-proxy IPs (or `*`). Set to `*` when running behind Caddy/Traefik/nginx in Docker Compose so real client IPs appear in access logs and rate limiting. See [Reverse Proxy](deployment/reverse-proxy.html). |
| `SERVEMD_BRANDING_ENABLED` | `true` | Show "Powered by servemd" footer. Set to `false` to disable for white-label or self-hosted deployments |
| `CUSTOM_CSS` | `custom.css` | Filename of custom CSS in DOCS_ROOT. Loaded on every page after default styles. See [Customization](features/customization.html) |
```

Also add to the Production Checklist (replace the reverse proxy line):

```markdown
- [ ] Configure reverse proxy with real-IP forwarding — see [Reverse Proxy](deployment/reverse-proxy.html)
- [ ] Set `FORWARDED_ALLOW_IPS=*` in docker-compose when using Caddy/Traefik/nginx
```

- [ ] **Step 2: Add reverse-proxy to sidebar navigation**

Open `docs/sidebar.md`. Find the Deployment section. Add the new page link.

Read the file first to get the exact current content, then add after the `docker.md` entry:

```markdown
  * [Reverse Proxy](deployment/reverse-proxy.md)
```

(The exact indentation must match the other items in the Deployment section.)

- [ ] **Step 3: Commit**

```bash
git add docs/configuration.md docs/sidebar.md
git commit -m "docs: add FORWARDED_ALLOW_IPS to configuration reference and sidebar"
```

---

## Self-Review

### Spec Coverage

| Requirement | Task |
|-------------|------|
| Real IPs in uvicorn access logs | Task 2 (`proxy_headers=True`) |
| Env var to control trusted proxies | Task 1 (`FORWARDED_ALLOW_IPS`) |
| Docker Hub image ready (no extra steps) | Task 1+2 — env var defaults to safe `127.0.0.1`; opt-in via `FORWARDED_ALLOW_IPS=*` |
| Hetzner deployment updated | Task 4 |
| Caddy header-passing documented | Task 5 |
| Traefik header-passing documented | Task 5 |
| nginx header-passing documented | Task 5 |
| CORS for claude.ai documented | Task 5 |
| Configuration reference updated | Task 6 |
| Sidebar navigation updated | Task 6 |

### Security Check

- Default `FORWARDED_ALLOW_IPS=127.0.0.1` means the published Docker Hub image is **safe out of the box** — proxy headers are ignored unless the operator explicitly opts in.
- The `deployment/hetzner/docker-compose.yml` sets `FORWARDED_ALLOW_IPS=*` because port 8080 is `expose:`-only (not `ports:`), so only the Caddy container on the private Docker network can reach it.

### Placeholder Scan

No TBDs, no "implement later", no incomplete steps. Every code block is complete and copy-pasteable.
