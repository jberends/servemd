# servemd Deployment on Hetzner VPS

Minimal secure Docker deployment with automatic container updates.

## Stack

- **servemd** — `jberends/servemd:latest` from Docker Hub (built-in docs)
- **Caddy** — Reverse proxy with automatic HTTPS (Let's Encrypt)
- **Auto-updates** — Cron job pulls latest images hourly

## Auto-updates (install after first deploy)

```bash
sudo bash /opt/servemd/install-update-cron.sh
```

## Quick Start

```bash
# On the VPS
cd /opt/servemd
docker compose up -d
```

Visit `http://YOUR_IP` — servemd docs are live.

## HTTPS (when CNAME is set)

1. Add CNAME(s): point your domain(s) to `static.109.5.225.46.clients.your-server.de`
2. Create `.env`:
   ```bash
   # Single domain
   echo "DOMAIN=docs.yourdomain.com" > .env

   # Multiple domains (space-separated)
   echo "DOMAIN=docs.example.com www.docs.example.com api.example.com" > .env
   ```
3. Restart Caddy:
   ```bash
   docker compose up -d caddy
   ```

Caddy obtains Let's Encrypt certificates for all listed domains.

## Automatic Updates

The cron job runs hourly and pulls the latest images for servemd and Caddy. If any image changed, `docker compose up -d` restarts the affected containers.

## Custom Docs

To serve your own documentation, mount a volume:

```yaml
# In docker-compose.yml, add to servemd service:
volumes:
  - /opt/servemd/docs:/app/__docs__:ro
```

Ensure your docs have `index.md`, `sidebar.md`, and `topbar.md`.

## Security

- servemd runs as non-root user (built into image)
- Caddy handles TLS termination
- Firewall: allow 22 (SSH), 80 (HTTP), 443 (HTTPS)
- Watchtower uses Docker socket (required for updates)
