# Phase 1 (DB + Migrations) - Local Dev

## Prereqs
- Docker + Docker Compose
- Python 3.10+ (recommended 3.11)

## 1) Start Postgres (and optional MinIO/Redis)
From repo root:
```bash
docker compose -f infra/docker-compose.yml up -d