# Docker Deployment Guide

Get the Personal Investment System running in under 2 minutes with Docker.

## Quick Start

```bash
# Clone and run
git clone https://github.com/yourusername/personal_investment_system.git
cd personal_investment_system
docker-compose up -d
```

**Access**: http://localhost:5000

On first launch, choose:
1. **Demo Mode** - Explore with sample data
2. **Upload Data** - Import your CSV/Excel files
3. **Skip** - Start with empty dashboard

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PIS_PORT` | 5000 | Host port |
| `SECRET_KEY` | auto | Flask session key |
| `DEMO_MODE` | false | Force demo mode |
| `LOG_LEVEL` | INFO | Logging verbosity |
| `TZ` | UTC | Timezone |

### Examples

```bash
# Change port
PIS_PORT=8080 docker-compose up -d

# Production with secret key
SECRET_KEY=$(openssl rand -hex 32) docker-compose up -d

# Demo mode
DEMO_MODE=true docker-compose up -d
```

---

## Commands Cheatsheet

```bash
# Start/Stop
docker-compose up -d          # Start in background
docker-compose down           # Stop (keeps data)
docker-compose restart        # Restart

# Monitoring
docker-compose logs -f        # View logs
docker-compose ps             # Check status
curl localhost:5000/health    # Health check

# Maintenance
docker-compose build          # Rebuild image
docker-compose exec pis-web bash  # Shell access

# Updates
git pull && docker-compose up -d --build
```

---

## Data Persistence

Data is stored in Docker volume `pis-investment-data`.

### Backup

```bash
docker run --rm \
  -v pis-investment-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/backup-$(date +%Y%m%d).tar.gz -C /data .
```

### Restore

```bash
docker run --rm \
  -v pis-investment-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/backup-YYYYMMDD.tar.gz -C /data
```

### Reset

```bash
docker-compose down -v        # Remove all data
docker-compose up -d          # Fresh start
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 5000 in use | `PIS_PORT=8080 docker-compose up -d` |
| Permission denied | `sudo chown -R 1000:1000 ./logs ./output` |
| Container won't start | `docker-compose logs pis-web` |
| Slow performance | Increase Docker Desktop memory to 4-6GB |

---

## Architecture

The Docker setup uses production-ready patterns:

- **Multi-stage build**: Reduces image size (~400MB vs ~1.5GB)
- **Non-root user**: Runs as `appuser` (UID 1000) for security
- **Health checks**: Automatic container health monitoring
- **Volume separation**: Persistent data survives rebuilds

### File Structure

```
docker/
├── Dockerfile        # Multi-stage build
└── entrypoint.sh     # Initialization script
docker-compose.yml    # Orchestration config
.dockerignore         # Build context filter
```

---

## Best Practices

### Resource Allocation (Docker Desktop)

- **CPUs**: 4+ recommended
- **Memory**: 4-6GB for large datasets
- **Swap**: 1GB

### Security

```bash
# Always set SECRET_KEY in production
SECRET_KEY=$(openssl rand -hex 32) docker-compose up -d
```

### Cleanup

```bash
docker system prune           # Remove unused containers
docker system prune -a        # Deep clean (reclaims GBs)
```

---

## Support

- Issues: https://github.com/yourusername/personal_investment_system/issues
- Docs: See `docs/` folder
