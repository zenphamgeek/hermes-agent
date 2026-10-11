# P15 Infrastructure — Service Endpoints

## Internal Services (10.123.214.0/24)

| Service | Container | IP:Port | Credentials |
|---|---|---|---|
| LM Studio (LLM) | HOST | `10.123.214.1:1234` | none (api_key=`lm-studio`) |
| PostgreSQL 16 | `postgres-ai` | `10.123.214.220:5432` | per-db users |
| Redis 7 | `redis-cache` | `10.123.214.184:6379` | pw: `redis_p15_2026` |
| MinIO S3 | `minio-s3` | `10.123.214.249:9000` | `minioadmin` / `minio_p15_2026` |
| Open WebUI | `openwebui` | `10.123.214.47:3080` | `admin@thapsang.com` |
| n8n | `n8n` | `10.123.214.64:5678` | — |
| Windmill | `windmill` | `10.123.214.120:8000` | `admin@windmill.dev` |
| ComfyUI | `comfyui` | `10.123.214.153:8188` | — |
| FaceFusion | `facefusion` | `10.123.214.208:7860` | — |
| OmniVoice TTS | `omnivoice` | `10.123.214.178:8080` | — |
| Grafana | `grafana` | `10.123.214.193:3030` | `admin` / `grafana_p15_2026` |
| Prometheus | `prometheus` | `10.123.214.193:9090` | — |
| Odoo 19 | `odoo` | `10.123.214.127:8069` | `admin` / `admin` |
| Cloudflare Proxy | `cloudflare-proxy` | `10.123.214.131` | — |

## Public Domains (Cloudflare Tunnel)

| Domain | Backend |
|---|---|
| `chat.thapsang.com` | Open WebUI |
| `chatbox.thapsang.com` | Chatbox |
| `odoo.thapsang.com` | Odoo 19 |
| `n8n.thapsang.com` | n8n |
| `windmill.thapsang.com` | Windmill |
| `comfyui.thapsang.com` | ComfyUI |
| `grafana.thapsang.com` | Grafana |
| `facefusion.thapsang.com` | FaceFusion |
| `tts.thapsang.com` | OmniVoice TTS |
| `s3console.thapsang.com` | MinIO Console |

## Database Credentials

| Database | User | Password | pgvector |
|---|---|---|---|
| `app_db` | `app_user` | `app_p15_2026` | ✅ |
| `vector_store` | `app_user` | `app_p15_2026` | ✅ |
| `openwebui_db` | `openwebui` | `openwebui_p15_2026` | ✅ |
| `windmill_db` | `windmill` | `windmill_p15_2026` | ✅ |
| `n8n_db` | `n8n_user` | `n8n_p15_2026` | — |
| `grafana_db` | `grafana` | `grafana_p15_2026` | — |
| `comfyui_db` | `comfyui` | `comfyui_p15_2026` | — |
| `odoo` | `odoo` | `odoo_p15_2026` | — |

## MinIO S3 Buckets

| Bucket | Purpose |
|---|---|
| `shared-assets` | General purpose (use for new projects) |
| `pg-backups` | Daily PostgreSQL dumps (auto-expire 30d) |
| `comfyui-outputs` | Generated images |
| `comfyui-models` | Model cache |
| `facefusion-io` | Face swap files |
| `omnivoice-audio` | TTS audio cache |
| `windmill-assets` | Workflow assets |
| `n8n-files` | Automation files |
| `grafana-exports` | Dashboard exports |

## Connection String Templates

```
# PostgreSQL
postgresql://<user>:<password>@10.123.214.220:5432/<database>

# Redis
redis://:redis_p15_2026@10.123.214.184:6379

# MinIO S3
endpoint_url=http://10.123.214.249:9000
aws_access_key_id=minioadmin
aws_secret_access_key=minio_p15_2026

# LM Studio (OpenAI-compatible)
base_url=http://10.123.214.1:1234/v1
api_key=lm-studio
```
