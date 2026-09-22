# SahayakAI — Production Deployment Guide

**Status:** APPROVED  
**Baseline Date:** 2026-09-23  
**Phase:** STEP 14 — Deployment & Operations  

---

## 1. Deployment Architecture

SahayakAI is partitioned into a decoupled frontend Single Page Application (SPA) and an asynchronous Python ASGI backend service:

```mermaid
graph LR
    Browser[Client Browser] -->|Port 443 / 80| Ingress[Reverse Proxy: Nginx / Cloudflare]
    Ingress -->|Static Assets| FE[Frontend Static Files / Vite Build]
    Ingress -->|/api/* Requests| BE[FastAPI / Uvicorn Service: Port 8000]
    BE --> DB[(Database: PostgreSQL / SQLite)]
    BE --> Storage[(Disk Storage: uploads/)]
```

---

## 2. Environment Setup

### 2.1 Backend Environment Variables (`.env`)
```bash
ENVIRONMENT=production
APP_NAME=SahayakAI
DATABASE_URL=postgresql://sahayak_user:secure_password@postgres-db:5432/sahayak_prod
DEFAULT_AI_PROVIDER=demo
OPENAI_API_KEY=
GEMINI_API_KEY=
CORS_ORIGINS=https://sahayakai.example.com
UPLOAD_DIR=/var/data/sahayakai/uploads
MAX_UPLOAD_SIZE_BYTES=10485760
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.35
```

### 2.2 Frontend Environment Variables (`frontend/.env.production`)
```bash
VITE_API_BASE_URL=https://sahayakai.example.com/api
```

---

## 3. Production Build Instructions

### 3.1 Build Frontend Bundle
```bash
cd frontend
npm ci
npm run build
# Generates production artifacts in frontend/dist/
```

### 3.2 Prepare Backend Environment
```bash
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Reverse Proxy Configuration (Nginx)

Example production Nginx virtual host configuration:

```nginx
server {
    listen 80;
    server_name sahayakai.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name sahayakai.example.com;

    ssl_certificate /etc/letsencrypt/live/sahayakai.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sahayakai.example.com/privkey.pem;

    # Client body upload limit (10MB document uploads)
    client_max_body_size 12M;

    # Serve static frontend SPA
    root /var/www/sahayakai/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API traffic to FastAPI ASGI server
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
    }

    # OpenAPI documentation endpoints
    location ~ ^/(docs|redoc|openapi.json) {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

---

## 5. Process Supervision (Systemd)

Example Systemd service unit for the FastAPI backend (`/etc/systemd/system/sahayakai.service`):

```ini
[Unit]
Description=SahayakAI Backend Service
After=network.target postgresql.service

[Service]
Type=simple
User=sahayak
WorkingDirectory=/var/www/sahayakai
EnvironmentFile=/var/www/sahayakai/.env
ExecStart=/var/www/sahayakai/.venv/bin/gunicorn backend.app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/sahayakai/access.log \
    --error-logfile /var/log/sahayakai/error.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## 6. Hardware & Resource Sizing

* **CPU**: Minimum 2 vCPUs recommended for sentence-transformers embedding generation.
* **RAM**: Minimum 2 GB RAM (SentenceTransformer `all-MiniLM-L6-v2` consumes ~300MB resident memory).
* **Storage**: Fast SSD recommended for document uploads and SQLite / PostgreSQL data files.
* **Network**: Low latency connection recommended if external AI providers (OpenAI / Gemini) are enabled.\n