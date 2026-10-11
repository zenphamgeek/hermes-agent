---
title: "P15 Infra Ops — Operate local P15 infrastructure, containers, and DBs"
sidebar_label: "P15 Infra Ops"
description: "Operate local P15 infrastructure, containers, and DBs"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# P15 Infra Ops

Operate local P15 infrastructure, containers, and DBs.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/infrastructure/p15-infra-ops` |
| Path | `optional-skills/infrastructure/p15-infra-ops` |
| Version | `1.0.0` |
| Author | hermes-community |
| License | MIT |
| Platforms | cli, telegram, windows |
| Tags | `p15 infra ops` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# P15 Infrastructure Operations

Manage the local P15 ThinkPad infrastructure: LXD containers, PostgreSQL 16
with pgvector, Redis cache, MinIO S3 object storage, LM Studio LLM backend,
and Cloudflare tunnel routing.

## When to Use

Activate this skill when the user asks to:
- Check, restart, or troubleshoot LXD containers
- Query or manage PostgreSQL databases
- Check Redis cache status or flush keys
- Upload/download files from MinIO S3
- Check LM Studio LLM availability or loaded model
- Manage Cloudflare tunnel or public domain routing
- Create new databases, users, or S3 buckets
- Check GPU VRAM usage or GPU time-sharing status

Do NOT use for cloud infrastructure (AWS, GCP, Azure) or non-P15 machines.

## Prerequisites

1. **LXD** installed on the P15 host
2. **Access** to the `10.123.214.0/24` LXD bridge network
3. **LM Studio** running on the host at `http://10.123.214.1:1234`
4. **psql**, **redis-cli**, and **mc** (MinIO client) available

## How to Run

All operations are executed via `terminal` tool with shell commands targeting
LXD containers or local services directly.

## Procedure

### Step 1 — Container Status Check

```bash
# List all containers with status
terminal(command="lxc list --format=csv -c ns4 2>/dev/null | column -t -s,")

# Check specific container
terminal(command="lxc info postgres-ai | head -20")

# Get container IP
terminal(command="lxc list postgres-ai --format=csv -c 4 | cut -d' ' -f1")
```

### Step 2 — Database Operations

```bash
# Connect to PostgreSQL
terminal(command="PGPASSWORD=app_p15_2026 psql -h 10.123.214.220 -U app_user -d app_db -c 'SELECT version();'")

# List all databases
terminal(command="PGPASSWORD=app_p15_2026 psql -h 10.123.214.220 -U app_user -d app_db -c '\\l'")

# Create new database
terminal(command="lxc exec postgres-ai -- sudo -u postgres psql -c \"CREATE USER myapp WITH PASSWORD 'myapp_pass'; CREATE DATABASE myapp_db OWNER myapp;\"")

# Enable pgvector
terminal(command="lxc exec postgres-ai -- sudo -u postgres psql -d myapp_db -c 'CREATE EXTENSION IF NOT EXISTS vector;'")
```

### Step 3 — Redis Operations

```bash
# Check Redis status
terminal(command="redis-cli -h 10.123.214.184 -a redis_p15_2026 ping")

# Check memory usage
terminal(command="redis-cli -h 10.123.214.184 -a redis_p15_2026 info memory | head -10")

# List keys by pattern
terminal(command="redis-cli -h 10.123.214.184 -a redis_p15_2026 keys '*pattern*' | head -20")

# Flush a database
terminal(command="redis-cli -h 10.123.214.184 -a redis_p15_2026 -n 0 flushdb")
```

### Step 4 — MinIO S3 Operations

```bash
# Setup alias (one-time)
terminal(command="mc alias set p15 http://10.123.214.249:9000 minioadmin minio_p15_2026")

# List buckets
terminal(command="mc ls p15/")

# Upload file
terminal(command="mc cp /path/to/file p15/shared-assets/")

# Download file
terminal(command="mc cp p15/shared-assets/filename /local/path/")

# Create new bucket
terminal(command="mc mb p15/new-bucket-name")
```

### Step 5 — LLM Backend Check

```bash
# Check LM Studio is running
terminal(command="curl -s http://10.123.214.1:1234/v1/models | python3 -m json.tool 2>/dev/null | head -20")

# Quick inference test
terminal(command="curl -s http://10.123.214.1:1234/v1/chat/completions -H 'Content-Type: application/json' -d '{\"model\":\"default\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":10}' | python3 -m json.tool")

# Check GPU usage
terminal(command="nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv 2>/dev/null || echo 'nvidia-smi not available'")
```

### Step 6 — Cloudflare Tunnel Management

```bash
# Check tunnel status (from proxy container)
terminal(command="lxc exec cloudflare-proxy -- systemctl status cloudflared")

# View current tunnel routes
terminal(command="lxc exec cloudflare-proxy -- cat /etc/cloudflared/config.yml 2>/dev/null | head -30")

# Test public domain
terminal(command="curl -sI https://chat.thapsang.com | head -5")
```

## Quick Reference

```
# Container management
lxc list                               # All containers
lxc exec <ct> -- bash                  # Shell into container
lxc restart <ct>                       # Restart container

# PostgreSQL
psql -h 10.123.214.220 -U app_user -d app_db   # Connect
\l                                               # List databases
\dt                                              # List tables

# Redis
redis-cli -h 10.123.214.184 -a redis_p15_2026   # Connect
info memory                                      # Memory stats
keys '*'                                         # All keys

# MinIO
mc ls p15/                             # List buckets
mc cp file p15/bucket/                 # Upload
mc cp p15/bucket/file ./               # Download

# LLM
curl http://10.123.214.1:1234/v1/models          # Available models
nvidia-smi                                       # GPU status
```

## Common Pitfalls

1. **Deploying Ollama**: NEVER deploy Ollama. LM Studio is the ONLY LLM backend.
2. **GPU contention**: Only ONE GPU-heavy task at a time. LM Studio has priority.
3. **Wrong database credentials**: Each database has its own user — check the table.
4. **Container IP changes**: LXD IPs are static on `10.123.214.0/24` — they don't change.
5. **Redis password**: Always use `-a redis_p15_2026` when connecting.
6. **MinIO alias**: Must `mc alias set p15 ...` before using `mc` commands.

## Verification

After infrastructure changes:
1. `lxc list` — all containers running
2. `curl http://10.123.214.1:1234/v1/models` — LLM responding
3. `redis-cli ping` — Redis alive
4. `mc ls p15/` — MinIO accessible
5. `psql -c 'SELECT 1'` — PostgreSQL reachable
