# Docker Guide & Best Practices

## Personal Investment System

This guide provides an introduction to Docker as used in this project, explaining core concepts, daily workflows, and best practices for maintenance and security.

---

## 1. Quick Concept Overview

Docker allows us to package the application with all its dependencies (Python, system libraries like `libopenblas`) into a standardized unit called a **Container**.

- **Image**: The "blueprint" or "template". It's read-only.
  - *Analogy*: A class definition in Python (`class InvestmentSystem:`).
- **Container**: A running instance of an Image. It has its own isolated file system and memory.
  - *Analogy*: An object instance (`sys = InvestmentSystem()`).
- **Volume**: A persistent storage area that survives when containers are destroyed.
  - *Usage*: Stores the SQLite database (`investment_system.db`) and user uploads.
- **Bind Mount**: A direct link between a folder on your Mac and a folder in the container.
  - *Usage*: Linking `./logs` so you can read logs on your Mac without entering the container.
- **Docker Compose**: A tool to define and run multi-container applications using a YAML file.
  - *Usage*: One command (`docker-compose up`) to handle network, volumes, and ports automatically.

---

## 2. Project Architecture

Your system uses a **Production-Ready** Docker configuration:

1. **Multi-Stage Build** (`Dockerfile`):
    - **Stage 1 (Builder)**: Installs heavy compilers (`gcc`, `g++`) to build Python packages.
    - **Stage 2 (Runtime)**: Copies only the ready-to-run artifacts to a slim Python image.
    - *Benefit*: Reduces image size (from ~1.5GB to ~400MB) and removes dangerous build tools from the runtime.

2. **Security First**:
    - **Non-Root User**: The app runs as `appuser` (UID 1000), not `root`. This limits damage if the container is compromised.
    - **Read-Only Mounts**: Configuration and demo data are mounted as read-only (`:ro`), preventing accidental deletion.

3. **Data Persistence**:
    - **Volume**: `pis-investment-data` creates a safe harbor for your database.
    - **Bind Mounts**: `logs/` and `output/` are mirrored to your host machine for easy access.

---

## 3. Daily Workflow Cheatsheet

### Starting & Stopping

```bash
# Start in background (detached mode)
docker-compose up -d

# Stop containers (preserves data)
docker-compose stop

# Stop and remove containers (preserves volumes/data)
docker-compose down
```

### Monitoring

```bash
# View real-time logs
docker-compose logs -f

# Check running status & ports
docker-compose ps

# Monitor resource usage (CPU/RAM)
docker stats
```

### Maintenance

```bash
# Rebuild image (after changing requirements.txt or Dockerfile)
docker-compose build --no-cache

# Update & Restart
git pull
docker-compose up -d --build
```

### Interactive Debugging

```bash
# Open a shell INSIDE the container
docker-compose exec pis-web /bin/bash

# Once inside, you can run manual Python commands:
python main.py run-all
```

---

## 4. Best Practices

### A. Resource Management (Docker Desktop)

Since you are on Apple Silicon (M-series):

1. Open **Docker Desktop Dashboard**.
2. Go to **Settings** (Gear icon) -> **Resources**.
3. **Recommendations**:
    - **CPUs**: 4 (Default is often 2, which can be slow for Pandas)
    - **Memory**: 4GB - 6GB (Crucial for `scipy` and large Excel files)
    - **Swap**: 1GB (Safety net)
4. **Virtualization Framework**: Ensure "Use Apple Virtualization framework" is checked for best performance.

### B. Cleaning Up

Docker accumulates "dangling" images (old versions) over time.

```bash
# Safe cleanup: Removes stopped containers and unused networks
docker system prune

# Deep cleanup: Removes ALL unused images (reclaims GBs of space)
docker system prune -a
```

*Recommendation: Run a safe cleanup once a month.*

### C. Security Hygiene

- **Secret Keys**: Never hardcode production secrets. Pass them via environment variables:

  ```bash
  SECRET_KEY=my-super-secure-key docker-compose up -d
  ```

- **Updates**: Regularly update the base image.
  - Edit `Dockerfile`: grep for `FROM python:3.11-slim-bookworm` and check mostly for security updates.

### D. Data Safety

- **Backups**: The `pis-investment-data` volume is internal to Docker.
- **Backup Command**:

  ```bash
  # Creates a tarball of your data in the current directory
  docker run --rm -v pis-investment-data:/data -v $(pwd):/backup alpine tar czf /backup/pis-backup-$(date +%Y%m%d).tar.gz -C /data .
  ```

---

## 5. Troubleshooting Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **"Bind mount failed"** | Mac File Sharing permissions | Check Docker Desktop Settings -> Resources -> File Sharing. Ensure user folder is added. |
| **"Port 5000 allocated"** | Python/AirPlay using port | `PIS_PORT=5001 docker-compose up -d` |
| **"Connection Refused"** | Container starting up | Wait 10s. Run `docker-compose logs` to see if it crashed. |
| **Slow Performance** | File sync overhead | Docker file sharing on Mac has overhead. Moving DB to named volume (done in this setup) solves 90% of this. |

---

## 6. Project Specific Tips

- **Demo Mode**: To force the demo mode for testing:
  `DEMO_MODE=true docker-compose up -d`
- **Translations**: If you change `.po` files, you must restart the container to recompile them at startup (the entrypoint script handles this).
