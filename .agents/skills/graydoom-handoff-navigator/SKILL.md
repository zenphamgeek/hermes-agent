---
name: graydoom-handoff-navigator
description: >-
  Multi-Worktree & Multi-Branch Project Handoff Orchestrator for transitioning
  Gray Doom from Codex to AGY & AGY-Fleet Pro Swarm (gemini-4-argon-high).
  Audits and synchronizes main, codex/settlement-art-mapping-20261015,
  codex/gameplay-resume-20261013, codex/game-art-atlas-parallel-20261008,
  codex/game-art-checkpoints-20260926, and the Novel/Dossier branch gemini-2
  with zero commit loss, uncommitted change packaging, and SecondBrain ADR
  compilation.
---

# Gray Doom Codex-to-AGY Handoff & Multi-Branch Navigator (`graydoom-handoff-navigator`)

Quy trình bàn giao không độ trôi (**Zero-Drift Handoff**) để chuyển giao dự án **Gray Doom** từ các nhánh làm việc của **Codex** sang **AGY & AGY-Fleet Pro Swarm (`tier="pro"`, `gemini-4-argon-high`)**, hợp nhất cả mảng **Gameplay / Settlement 2.5D / Game Art Atlas (`main` & `codex/*`)** lẫn mảng **Novel 176 Chương / 352 Scene Plates / 26 Character Dossiers (`gemini-2`)**.

---

## 1. Bản Đồ Địa Hình 4 Git Worktrees & 6 Nhánh Chủ Lực Hiện Tại

| Worktree / Đường Dẫn | Nhánh Git (`Branch`) | Commit HEAD | Vai Trò & Trạng Thái Hiện Tại |
| :--- | :--- | :--- | :--- |
| `/home/zen/Downloads/Graydoom` *(symlink `/home/zen/Graydoom`)* | `codex/game-art-checkpoints-20260926` *(và `main` tại `2cf1119d`)* | `cc70623f` | **Security & Source-Index Hardening**: Đã hoàn tất 8 vòng kiểm toán bảo mật (`ConnectionRegistry`, chống CWE-22/59/362/674 trên `build-content-source-index.py`), `graydoom-immutable-agent-harness-v1.md`. |
| `/home/zen/.codex/worktrees/1ec4/Graydoom` | `codex/settlement-art-mapping-20261015` *(kế thừa `codex/gameplay-resume-20261013` `64d98acc`)* | `a3aaa2f1` | **Live Codex Gameplay & Settlement 2.5D/WebGL**: Đã lên tới migration `077_world_gm_ban_history.sql`, đặt cutout art công trình lên 40 lô định cư 2.5D/WebGL, văn hóa mở rộng lãnh thổ, hủy quân, chợ NPC, tìm kiếm/khóa tài khoản GM. **Đang có bản nháp dở dang**: `migrations/078_world_gm_gold_adjustments.sql` & `docs/qa/registered-gm-gold-browser-2026-10-17.md`. |
| `/home/zen/Downloads/Graydoom-art-atlas` | `codex/game-art-atlas-parallel-20261008` | `27fd6ecf` | **2,081-Slot Game Art Atlas & Spatial Map**: Quản lý 2,081 đơn đặt hàng Art, xoay góc 5 Tần phi, kiểm định 72px công trình. **Đang có ứng viên dở dang**: `atlantic-city-center-imagegen-v1.png` & `.qa.md`. |
| `/home/zen/Downloads/Graydoom-novel` | `gemini-2` | `06ce2ad2` | **Novel 176 Chương, 352 Scene Plates & 26 Character Dossiers**: Đã hoàn tất 352 tranh chương truyện (`352/352 passing` tripwire), mở rộng hồ sơ 10-card cho Mei, Lucía, Evelyn, Zen, Ilya và 14 nhân vật phụ (Phase 2 V6), kèm cổng duyệt tự động `autonomous-fleet-art-harness.py`. |

---

## 2. Quy Trình 6 Bước Tiếp Quản Dự Án Từ Codex Sang AGY-Fleet (`Zero-Drift Handoff Protocol`)

### Bước 1 — Chạy Trình Kiểm Toán Bàn Giao Tự Động (`graydoom_codex_handoff_auditor.py`)
Luôn khởi đầu phiên làm việc bằng công cụ kiểm toán đa nhánh để chụp ảnh trạng thái đĩa thực tế (không đoán mò từ bộ nhớ hội thoại):
```bash
python3 /home/zen/hermes-agent/tools/graydoom_codex_handoff_auditor.py --write-report
```
Công cụ này tự động:
- Quét toàn bộ 4 worktrees và 6 nhánh (`main`, `codex/settlement-art-mapping-20261015`, `codex/gameplay-resume-20261013`, `codex/game-art-atlas-parallel-20261008`, `codex/game-art-checkpoints-20260926`, `gemini-2`).
- Liệt kê chính xác các file đang sửa dở (`modified` / `untracked`) của Codex.
- Đếm số lượng Change Packets (`config/development-harness/changes/gd-*.json`), số lượng SQL migrations (`migrations/*.sql`), và trạng thái sổ cái `gemini-2`.
- Sinh kế hoạch điều phối 4 cấp **Gemini 4 Argon (`tier="pro"`)** và xuất biên bản bàn giao vào Obsidian SecondBrain (`10-Areas/Architecture/Graydoom-Codex-to-AGY-Handoff.md`).

### Bước 2 — Đóng Gói & Hoàn Tất Các Tác Vụ Dở Dang Của Codex (In-Flight Closure)
Trước khi gộp nhánh hoặc phát triển tính năng mới, xử lý dứt điểm 2 tác vụ Codex đang làm dở trên các worktree:
1. **Trên `/home/zen/.codex/worktrees/1ec4/Graydoom` (`codex/settlement-art-mapping-20261015`)**:
   - Kiểm tra `migrations/078_world_gm_gold_adjustments.sql`, `docs/registered-gm-gold-adjustment-parity-spec.md`, và `docs/qa/registered-gm-gold-browser-2026-10-17.md`.
   - Tạo hoặc cập nhật packet `config/development-harness/changes/gd-registered-gm-gold-adjustment-v1.json`.
   - Chạy `node --test tests/world-gm-search.test.js && npm run verify:harness && npm run verify:content-sources` rồi commit gọn gàng.
2. **Trên `/home/zen/Downloads/Graydoom-art-atlas` (`codex/game-art-atlas-parallel-20261008`)**:
   - Kiểm tra `art/candidates/landscapes/atlantic-city-center-imagegen-v1.png` và `.qa.md`.
   - Chạy `python3 scripts/verify-settlement-spatial-map-candidate.py` và `python3 scripts/build-content-source-index.py --write`, sau đó thực hiện đúng **1 commit riêng lẻ** cho ứng viên này.

### Bước 3 — Bảo Toàn Ranh Giới Giữa Nhánh Engine (`main` / `codex/*`) và Nhánh Novel (`gemini-2`)
- **Tuyệt đối không `git merge` mù quáng** giữa `gemini-2` (chứa hàng trăm MB tranh minh họa chương truyện 16:9 và bản thảo 176 chương) vào nhánh Engine `codex/settlement-art-mapping-20261015` khi chưa qua cổng lọc `content/production-source-index-v1.json`.
- Giữ mô hình **Dual-Track Worktree Isolation**:
  - **Track A (Gameplay, 2.5D/WebGL Settlement & Runtime Game Art)**: Làm việc trên `/home/zen/.codex/worktrees/1ec4/Graydoom` (`codex/settlement-art-mapping-20261015`) và `/home/zen/Downloads/Graydoom-art-atlas` (`codex/game-art-atlas-parallel-20261008`), tiến tới fast-forward/merge có kiểm soát về `main`.
  - **Track B (Novel 176 Chương, 352 Scene Plates, 26 Character Dossiers & Review Portal)**: Làm việc trên `/home/zen/Downloads/Graydoom-novel` (`gemini-2`), đồng bộ một chiều các Identity Locks (`content/canonical-characters-v1.json`, `character-face-consistency-dna-v1.json`, và khuôn mặt chuẩn `main` branch `sunward-court-six-person-v3.png`) từ Track A sang Track B.

### Bước 4 — Phân Bổ Nhiệm Vụ Cho Cụm AGY-Fleet Pro Swarm Với Gemini 4 Argon (`tier="pro"`)
Mọi tác vụ phát triển tiếp theo sau Handoff đều được lập kế hoạch qua `fleet_plan(..., model="gemini-4-argon-high", tier="pro")` và điều phối qua 17 Standard Pro Nodes (`tier="pro"`):
- **Tổ Gameplay & Parity (`node-4`, `binhthuong`, `coderedgen` — `gemini-4-argon-high`)**:
  - Đóng các mục `PARTIAL` / `MISSING` trong `docs/travianz-parity-register.md` kèm packet `gd-<slug>.json` và unit tests `node --test`.
- **Tổ Settlement 2.5D/WebGL & Spatial Geometry (`sunward`, `insilos`, `justaskgao` — `gemini-4-argon-high`)**:
  - Hoàn thiện ánh xạ 40 lô định cư (`f1`–`f18`, `19`–`40`), hành lang đường/nước 31px và kiểm định `390×844` mobile browser QA.
- **Tổ Character Atlas & Novel `gemini-2` (`ai-digimate`, `codegeekvn`, `gaopham`, `agy-home` — `gemini-4-argon-high`)**:
  - Vận hành pipeline 2,081 slots (`build-game-art-atlas-work-orders.py`), kiểm định 1 mắt góc nghiêng (`ANG_PRF_90`), lề 11% alpha, khả đọc 72px, và cổng 6 trục `autonomous-fleet-art-harness.py`.

---

## 3. Lệnh Kiểm Tra Sức Khỏe Liên Nhánh (Cross-Worktree Health Check)

```bash
# 1. Kiểm toán toàn diện 4 worktrees & xuất báo cáo bàn giao
python3 /home/zen/hermes-agent/tools/graydoom_codex_handoff_auditor.py --write-report

# 2. Kiểm tra Harness & Tests trên nhánh Gameplay mới nhất của Codex
npm --prefix /home/zen/.codex/worktrees/1ec4/Graydoom run verify:harness
NODE_ENV=test node --test /home/zen/.codex/worktrees/1ec4/Graydoom/tests/development-harness.test.js

# 3. Kiểm tra 26 Character Dossiers & 2,081 Atlas Work Orders trên nhánh Art Atlas
node /home/zen/Downloads/Graydoom-art-atlas/scripts/verify-character-dossiers.js
python3 /home/zen/Downloads/Graydoom-art-atlas/scripts/build-game-art-atlas-work-orders.py --check

# 4. Kiểm tra 352 Scene Plates Tripwire trên nhánh Novel gemini-2
python3 /home/zen/Downloads/Graydoom-novel/tools/plate_tripwire.py
```
