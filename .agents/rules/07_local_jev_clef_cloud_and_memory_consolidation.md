# Master Rule 07: Local JEV + Clef Cloud Synergy, Memory Consolidation & Modal Fine-Tuning

> **Authority**: Multidisciplinary Advisory & Verification Council (Hội đồng Cố vấn & Kiểm định Đa ngành)  
> **Status**: Sovereign Invariant  
> **Scope**: All AI Agents, Subagents, Watchers, and Sidecars across `/home/zen/hermes-agent`, `/home/zen/O20`, `/home/zen/VerticalRisk`, `/home/zen/Graydoom`, and `/home/zen/insilos_mobile`.

---

## 1. Dual-Engine Synergy Invariant (Local JEV + Clef Cloud)
- **Local JEV Priority (Fast-Path & Zero-Cost)**:
  - Mọi tác vụ, prompt hoặc lệnh điều phối BẮT BUỘC phải qua Local JEV (`LocalJEVEvaluator`) sàng lọc cục bộ trên máy trạm trước khi thực hiện bất kỳ lệnh gọi ngoại biên nào.
  - Local JEV chịu trách nhiệm: Lọc bí mật (`SecretScrubber`), kiểm tra băm khử trùng lặp (cửa sổ 2 giờ), thẩm định cú pháp AST (`ast.parse`), kiểm tra file tồn tại, và gán test runner bản địa (`odoo-bin`, `node:test`, `pytest`, `flutter test`).
  - Nếu điểm phức tạp $< 2.2$ và bước thang tiến hóa $\le 2$: Phê duyệt thực thi cục bộ trực tiếp (*Fast-Path*), cấm lãng phí quota mô hình đám mây lớn.
- **Clef Cloud Escalation (Cognitive Expansion)**:
  - Khi điểm phức tạp $\ge 2.2$, hoặc bước thang $\ge 3$, hoặc tác vụ thuộc nhóm kiến trúc bảo mật/tiến hóa sâu: Bắt buộc chuyển tiếp lên **Clef Cloud Model** (Cloudflare Workers AI Edge PoPs kết hợp Modal Escalation).
  - Clef Cloud biên dịch `EnrichedExecutionSpecification`, triệu tập Hội đồng Phản biện (Dialect Council: Thesis $\to$ Antithesis $\to$ Synthesis) cùng Opus Node (`ultra-2` / `pro-1` / `claude-opus-4.8`).
  - Nghiêm cấm vi phạm **Zero-Output-Tokens Invariant** tại tầng Edge PoPs.

---

## 2. Magentic-UI Action Ledger & SSRF Shielding
- Mọi hành động ngoại biên (cào dữ liệu GitHub, ArXiv, hoặc dispatch qua Fleet) BẮT BUỘC phải ghi nhận một bản ghi bất biến có khóa luồng vào sổ cái `action_ledger.jsonl` (Magentic-UI Pattern).
- Phải che giấu credentials trên URL và lưu mã băm SHA256 của payload đã thanh lọc bí mật.
- Nghiêm cấm truy cập mạng không qua `SSRFGuard`: cấm dải IP private (RFC 1918), loopback (đối với external radar), multicast, và Cloud Metadata IMDS (`169.254.169.254`). Chỉ cho phép các host được chứng nhận (`export.arxiv.org`, `api.github.com`, `github.com`) hoặc localhost port 7777 cho Fleet.

---

## 3. Clef Mnemosyne Memory & Agent Rule Consolidation
- Bộ nhớ vận hành theo 3 cấp độ chặt chẽ:
  - **L1 (Episodic)**: Transcript và logs (`transcript.jsonl`, `fleet_watcher_state.json`), vòng đời 6h.
  - **L2 (Semantic)**: Bài học đúc kết, kinh nghiệm thành bại theo domain lưu tại `evolution_ledger.db` và `action_ledger.jsonl`.
  - **L3 (Normative)**: Hệ thống quy tắc cốt lõi (`AGENTS.md`, `.agents/rules/`, `~/.gemini/config/rules/`).
- **Bi-Temporal Tombstone Invariant (Cấm Xóa Ngầm)**:
  - Tuyệt đối KHÔNG xóa ngầm (*Silent Delete*) các dòng quy tắc hoặc tri thức cũ.
  - Khi bãi bỏ hoặc thay thế quy tắc, BẮT BUỘC ghi bản ghi tombstone vào `resources/l3_tombstones.jsonl` với đầy đủ `valid_from`, `valid_to`, `reason`, `superseded_by`, và `evidence`.
- **Lịch Trình Hợp Nhất Định Kỳ**:
  - Hàng ngày 04:15 ICT (`rule-harness-daily-consolidation` sidecar): Hợp nhất kinh nghiệm L2 và dọn dẹp các quy tắc lỗi thời.
  - Chủ nhật 03:00 ICT (`memory-curator-l3-audit` sidecar): Chạy `curate_l3.py --apply` tuân thủ nghiêm ngặt 7 điều kiện của Auto-Apply Gate (§4.1).

---

## 4. Modal JEV Fine-Tuning Standard
- Dữ liệu huấn luyện tinh chỉnh Local JEV được tự động thu hoạch định kỳ từ `action_ledger.jsonl` và `evolution_ledger.db` qua `tools/modal_jev_finetuning.py --harvest-dataset`.
- Huấn luyện tinh chỉnh thực thi trên Modal Multi-GPU (NVIDIA T4 / A10G) sử dụng **QLoRA 4-bit (NF4)** với ngân sách khống chế $< \$0.45$/lần chạy ($\le 45$ phút).
- Trọng số sau huấn luyện phải được xuất về định dạng `ONNX` và `GGUF` nạp lại cho máy trạm ThinkPad để đảm bảo 100% khả năng quyết định cục bộ tức thì (<20ms).
