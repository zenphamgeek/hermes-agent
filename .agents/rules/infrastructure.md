# P15 Infrastructure Rules

## Critical Rules — Read First

1. **LLM**: ONLY use LM Studio at `http://10.123.214.1:1234/v1` — NEVER deploy Ollama or any other LLM server
2. **No new LXD containers without asking** — all infrastructure is pre-deployed
3. **Credentials are real** — handle with care, never expose in logs/commits
4. **All containers share `10.123.214.0/24` subnet** — use IPs directly for internal calls

## LLM Backend

| Property | Value |
|---|---|
| Type | LM Studio (runs on HOST, NOT in any container) |
| API | `http://10.123.214.1:1234/v1` (OpenAI-compatible) |
| GPU | Quadro RTX 5000 (16GB VRAM) |
| VRAM Reserved | ~11GB for LLM inference |

```python
from openai import OpenAI
client = OpenAI(base_url="http://10.123.214.1:1234/v1", api_key="lm-studio")
```

## Core Services

| Service | IP:Port | Credentials |
|---|---|---|
| PostgreSQL 16 + pgvector | `10.123.214.220:5432` | see per-db users |
| Redis | `10.123.214.184:6379` | `redis_p15_2026` |
| MinIO S3 | `10.123.214.249:9000` | `minioadmin / minio_p15_2026` |
| Open WebUI | `10.123.214.47:3080` | `admin@thapsang.com` |
| Odoo 19 | `10.123.214.127:8069` | `admin / admin` |

## Database Quick Reference

| Database | User | For |
|---|---|---|
| `app_db` | `app_user` / `app_p15_2026` | General purpose (has pgvector) |
| `vector_store` | `app_user` / `app_p15_2026` | Vector embeddings (has pgvector) |
| `openwebui_db` | `openwebui` / `openwebui_p15_2026` | Open WebUI |
| `odoo` | `odoo` / `odoo_p15_2026` | Odoo ERP |

## Public Domains (Cloudflare Tunnel)

All `*.thapsang.com` → `10.123.214.131` (cloudflare-proxy) → routed by Nginx SNI

| Domain | Service |
|---|---|
| `chat.thapsang.com` | Open WebUI |
| `odoo.thapsang.com` | Odoo 19 |
| `n8n.thapsang.com` | n8n |
| `grafana.thapsang.com` | Grafana |

## Rules for New Services

1. Database: Create new user+db in `postgres-ai` OR use `app_db`
2. Cache: Use Redis at `10.123.214.184:6379`
3. File storage: Use MinIO `shared-assets` bucket
4. LLM: Point to `http://10.123.214.1:1234/v1`
5. Public URL: Add Cloudflare tunnel ingress via `proxy.thapsang.com` UI

## GPU Time-Sharing

1. LM Studio has PRIORITY — always loaded
2. Only ONE GPU-heavy task at a time (ComfyUI OR FaceFusion OR OmniVoice)
3. Large models (>11GB) may cause GPU container OOM
