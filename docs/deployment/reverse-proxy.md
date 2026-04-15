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
