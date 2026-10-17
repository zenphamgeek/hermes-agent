# Rule 05: Modal Multi-GPU Fleet Management & Token Security Invariants

> **Sovereign Principle**: Never mutate, delete, or rotate master tokens without explicit author consent. Maintain 15-Workspace Registry integrity and orchestrate parallel GPU workloads via Round-Robin load-balancing across active fleet profiles.

---

## 1. Master Token Security & Immutability Invariant

### 1.1. Explicit Protection Mandate
In accordance with the directive in `modal_token_profile.md` (*"Đừng xóa hay ROtate, tôi tự bảo mật"*):
- **NEVER** run `modal token set` or delete entries in `modal_token_profile.md` or `~/.modal.toml` autonomously.
- **NEVER** commit plain secret tokens (`as-...`) to public git repositories or unredacted log files.
- All secrets displayed in public reports, logs, or UI summaries **MUST** be masked (e.g. `as-JSRb...prlN`).

---

## 2. 15-Workspace Registry & 9-Profile Runtime Fleet Architecture

The Modal cloud compute capacity is structured across two distinct tiers:

### 2.1. 15-Workspace Master Registry
15 independent workspace profiles distributed across 2 Pro accounts:
- **`just.ask.mr.zen@gmail.com`**:
  1. `default` (Master Account Profile) — `[REDACTED_MODAL_TOKEN_ID]`
  2. `zenpeace` (Video SF / Model Endpoint) — `[REDACTED_MODAL_TOKEN_ID]`
  3. `zenguru` (Video SF / Model Endpoint) — `[REDACTED_MODAL_TOKEN_ID]`
  4. `mindful` (Video SF / Model Endpoint) — `[REDACTED_MODAL_TOKEN_ID]`
- **`nhatrophamvu@gmail.com`**:
  5. `asmr` (Image / Video API) — `[REDACTED_MODAL_TOKEN_ID]`
  6. `pvvsf` (SwapFace Production) — `[REDACTED_MODAL_TOKEN_ID]`
  7. `vi2vi` (SwapFace / Image SF) — `[REDACTED_MODAL_TOKEN_ID]`
  8. `phi4` (LLM Inference) — `[REDACTED_MODAL_TOKEN_ID]`
  9. `default` (Sub-account Root) — `[REDACTED_MODAL_TOKEN_ID]`
  10. `zenllm` (General GPU / LLM) — `[REDACTED_MODAL_TOKEN_ID]`
  11. `zennchat` (General GPU / Chat) — `[REDACTED_MODAL_TOKEN_ID]`
  12. `r2rgraph` (Active Default Fleet) — `[REDACTED_MODAL_TOKEN_ID]`
  13. `mvlm` (Multimodal Vision / SF) — `[REDACTED_MODAL_TOKEN_ID]`
  14. `motion` (Motion Geometry / SF) — `[REDACTED_MODAL_TOKEN_ID]`
  15. `vrag` (Video RAG / SF) — `[REDACTED_MODAL_TOKEN_ID]`
  *(Plus `diatts` `[REDACTED_MODAL_TOKEN_ID]` & `mojopham` `[REDACTED_MODAL_TOKEN_ID]`)*.

### 2.2. Active Runtime Fleet (9 Profiles)
The local workstation environment (`~/.modal.toml`) actively provisions 9 profiles for parallel execution:
`r2rgraph` (default), `motion`, `diatts`, `mojopham`, `mvlm`, `vrag`, `vi2vi`, `zenllm`, `zennchat`.

---

## 3. Workload Dispatch & Failover Contract

### 3.1. Round-Robin Multi-GPU Parallelism
Any batch GPU workload (such as multi-face video segment face-swapping or neural audio synthesis) MUST use round-robin assignment across all available profiles in `ALL_MODAL_PROFILES` to achieve up to 9x parallel throughput.

### 3.2. Automatic 429 & Quota Failover
When a remote worker encounters HTTP 429 (Rate Limit) or compute quota exhaustion:
1. Mark the current profile as `exhausted` for the current batch.
2. Automatically failover to the next healthy profile in the pool.
3. If all 9 active profiles are saturated, load standby profiles from the 15-Workspace master registry into `~/.modal.toml`.

### 3.3. Zombie Worker & Cost Guard
1. **Zero-Leaked-Containers**: After every batch dispatch completes or errors out, verify `modal container list --json` is empty (`[]`).
2. **Emergency Cleanup**: If runaway containers persist, invoke `bash scripts/kill_modal.sh --all` immediately.
3. **Usage Monitoring**: Run `python3 scripts/modal_fleet_monitor.py` to maintain audit logs in `output/modal_fleet_status.json`.

---

## 4. Modal GPU Remote Execution Credit Gate Invariant (Deploy > $15, Inference > $10)

Per sovereign decree, all remote Modal GPU operations across all pipelines, scripts, agents, and coordinators are bound by two strict credit thresholds:

### 4.1. Passive Mathematical Credit Calculation (0 Outbound Scraping)
$$\text{Committed Spend} = \text{Settled MTD Spend (via .modal\_billing\_ledger.json)} + \sum \text{Active In-Flight Leases}$$
$$\text{Remaining Credits} = \$30.00 - \text{Committed Spend}$$
- **Zero-Outbound-Scraping Invariant**: Credit gates MUST evaluate locally via passive cached ledger state (`.modal_billing_ledger.json`) combined with monotonic in-flight lease reservations (`tools/modal_budget_guard.py`: `$2.50` deploy lease / `$0.50` inference lease, enforced via `time.monotonic()` TTL and `idempotency_key` deduplication), generating **0 outbound HTTP billing scrape requests** during admission control to prevent `HTTP 429` rate-limiting.

### 4.2. Pre-Flight Execution Gates
1. **Deploy Gate (Strict > $15.00 Remaining Credits)**:
   - Any long-running app deployment (`modal deploy`, persistent worker, ComfyUI server, Live Avatar daemon) is **STRICTLY AND ABSOLUTELY FORBIDDEN** unless the target workspace has strictly **more than $15.00 USD in remaining credits** ($\text{Remaining Credits} > \$15.00 \iff \text{Committed Spend} < \$15.00$).
   - Any workspace with $\le \$15.00$ remaining credits is immediately rejected by admission control (`RuntimeError: Modal Credit Gate Violation`).
2. **Inference Gate (Strict > $10.00 Remaining Credits)**:
   - Any remote GPU inference job (`modal run`, webhook invocation, remote model execution) is **STRICTLY AND ABSOLUTELY FORBIDDEN** unless the target workspace has strictly **more than $10.00 USD in remaining credits** ($\text{Remaining Credits} > \$10.00 \iff \text{Committed Spend} < \$20.00$).
   - Any workspace with $\le \$10.00$ remaining credits is hard-blocked from receiving jobs (`RuntimeError: Modal Credit Gate Violation`).
3. **Hard-Kill Ceiling ($25.00 USD Watchdog)**:
   - If a workspace cost reaches $\ge \$25.00$, `tools/modal_budget_guard.py` automatically executes an emergency shutdown (`modal app stop` and `modal container stop`) within 30 seconds.
4. **Hermes-Clef-Decision Permanent Retirement**:
   - `hermes-clef-decision` on Modal GPU is permanently decommissioned. 100% of Clef cognitive pre-routing and classification tasks MUST resolve via Cloudflare Workers AI Cloud (@cf/cloudflare/clef-flash) or Local Air-Gapped Surrogate ($0.00 Modal GPU cost).


