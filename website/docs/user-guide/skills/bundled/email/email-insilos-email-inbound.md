---
title: "Insilos Email Inbound — Classify inbound email → Odoo CRM/PO/HSE + Telegram alert"
sidebar_label: "Insilos Email Inbound"
description: "Classify inbound email → Odoo CRM/PO/HSE + Telegram alert"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Insilos Email Inbound

Classify inbound email → Odoo CRM/PO/HSE + Telegram alert.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/email/insilos-email-inbound` |
| Version | `1.0.0` |
| Author | Insilos Enterprise, Hermes Agent |
| License | MIT |
| Platforms | linux, macos |
| Tags | `email`, `erp`, `odoo`, `crm`, `hse`, `inbound` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Insilos Email Inbound Skill (`insilos-email-inbound`)

Phân tích email đến, trích xuất thực thể hóa chất, phân loại nghiệp vụ (CRM lead / RFQ vendor / HSE SDS), POST envelope chuẩn vào Odoo ERP, và thông báo qua Telegram.

Webhook route `email-inbound` gọi skill này cho mỗi email đến. Agent là bộ não xử lý — thay thế pipeline script fake-AI cũ.

## When to Use

Skill này tự động chạy khi webhook route `email-inbound` nhận được email từ Gmail Pub/Sub push. Không dùng thủ công.

## Prerequisites

- Odoo ERP endpoint reachable: `http://10.123.214.220:8069`
- Odoo API key: `insilos_sec_key_2026_pubsub` (trong `X-ERP-API-Key` header)
- Gmail OAuth token tại `~/.hermes/gmail_token.json` (đã có)
- Webhook route `email-inbound` đã đăng ký với `--script fetch_gmail.py` và `--deliver telegram --deliver-chat-id 1431349185`
- Route subscription có `"toolsets": ["terminal"]` trong `webhook_subscriptions.json` (thêm thủ công)
- Scripts: `~/.hermes/scripts/fetch_gmail.py` (webhook route script), `~/.hermes/skills/email/insilos-email-inbound/scripts/post_odoo.py`

## How to Run

Skill chạy tự động qua webhook. Không chạy thủ công.

## Quick Reference

| Bước | Agent hành động | Tool |
|------|----------------|------|
| 1 | Đọc email payload (webhook `--script` đã fetch email từ Gmail API) | `read_file` (context) |
| 2 | Phân tích: trích sender, subject, body, tìm entity hóa chất | reasoning |
| 3 | Phân loại event_type: `email.inbound.crm_lead` / `email.inbound.vendor_quote` / `email.inbound.chemical_sds` | reasoning |
| 4 | Xây dựng JSON envelope theo spec ERP_PUBSUB_INTEGRATION_SPEC.md | `terminal` |
| 5 | POST envelope vào Odoo: `python3 ~/.hermes/scripts/post_odoo.py` | `terminal` |
| 6 | Thông báo Telegram: response summary (webhook `deliver: telegram` tự gửi) | response text |

## Procedure

### 1. Đọc email

Email payload đã được webhook `--script` fetch từ Gmail API. Nội dung trong `payload` context:

- `sender.name`, `sender.email`
- `subject`
- `body` (text/plain)
- `attachments[]` (nếu có: `file_name`, `sha256`, `path`)
- `gcp_message_id`, `history_id`

### 2. Phân tích & trích xuất thực thể

Từ nội dung email, xác định:

- **Tên hóa chất** (chemical_name) — VD: Toluene, Acetone, Xylene
- **Số CAS** (cas_number) — VD: 108-88-3
- **Số lượng & đơn vị** (quantity, unit) — VD: 50 tấn, 200 kg
- **Tổ chức gửi** (organization) — từ domain email
- **Địa điểm giao hàng** (delivery_location) — nếu được đề cập

### 3. Phân loại event_type

| event_type | Điều kiện | Hành động Odoo |
|-----------|-----------|----------------|
| `email.inbound.crm_lead` | Yêu cầu báo giá, hỏi hàng, thông tin sản phẩm | Tạo `crm.lead` |
| `email.inbound.vendor_quote` | Nhà cung cấp gửi báo giá, bảng giá, RFQ response | Cập nhật `purchase.order` |
| `email.inbound.chemical_sds` | MSDS, SDS, khai báo hóa chất, Nghị định 113 | Tạo `hse.chemical.declaration` |

### 4. Xây dựng JSON envelope

Tuân theo schema từ `docs/specs/ERP_PUBSUB_INTEGRATION_SPEC.md`:

```json
{
  "event_id": "evt-{timestamp}-{short_id}",
  "trace_id": "trc-{uuid}",
  "event_type": "email.inbound.crm_lead",
  "source": "gmail.pubsub",
  "timestamp": "{ISO 8601}",
  "priority": "HIGH" hoặc "NORMAL",
  "producer": "hermes-agent-event-bus",
  "payload": {
    "sender": {"name": "...", "email": "...", "organization": "..."},
    "recipient": "inteligentsilos@gmail.com",
    "subject": "...",
    "body": "...",
    "ai_analysis": {
      "summary": "tóm tắt 1-2 câu",
      "category": "INQUIRY_QUOTATION",
      "sentiment": "POSITIVE/NEUTRAL/NEGATIVE",
      "action_required": true/false,
      "entities": {
        "chemical_name": "...",
        "cas_number": "...",
        "quantity": 0,
        "unit": "Tons",
        "delivery_location": "..."
      }
    },
    "attachments": []
  }
}
```

### 5. POST envelope vào Odoo

```bash
echo '<envelope_json>' | python3 ~/.hermes/scripts/post_odoo.py
```

Script này POST tới `http://10.123.214.220:8069/api/v1/pubsub/ingest` với headers:
- `Content-Type: application/json`
- `X-ERP-API-Key: insilos_sec_key_2026_pubsub`
- `X-Hermes-Signature: sha256=<HMAC-SHA256 của body>`

Kiểm tra response. Nếu `status: "success"` → ghi nhận `target_model` + `target_id`.

### 6. Response

- Nếu xử lý thành công: trả về summary ngắn bằng tiếng Việt, VD: "📬 Đã tạo CRM lead từ email của &#123;sender&#125; - &#123;subject&#125; (ID: &#123;target_id&#125;)"
- Nếu email không có nội dung đáng xử lý (spam, auto-reply, không liên quan): trả về `[SILENT]`
- Nếu lỗi: mô tả ngắn lỗi + "cần kiểm tra thủ công"

## Pitfalls

- **Idempotency:** Odoo addon tự check `event_id` trùng trong `pubsub.event.log`. Luôn tạo `event_id` duy nhất mỗi lần. Dùng `gcp_message_id` làm seed.
- **Rate limit:** Gmail API 250 quota/giây/user. Script `fetch_gmail.py` chỉ fetch 1-5 message mỗi lần gọi. Không gọi lại trong cùng một webhook.
- **Gmail watch hết hạn 7 ngày:** Cron `0 3 * * 0` chạy `--setup-watch` để gia hạn.
- **Attachments lớn:** Skill hiện tại chỉ ghi nhận metadata (tên, hash, path). File vật lý lưu tại `~/.hermes/data/email-attachments/`. MinIO optional — chưa tích hợp.
- **Webhook safe toolset:** Route `email-inbound` cần `"toolsets": ["terminal"]` trong `webhook_subscriptions.json` (thêm thủ công, không qua `subscribe`). Nếu thiếu, agent không chạy được `post_odoo.py`.
- **HMAC secret:** Route secret được sinh tự động khi subscribe. Giữ bí mật. GCP push subscription dùng secret này trong `X-Webhook-Signature` header.

## Verification

- Gửi email test vào `inteligentsilos@gmail.com`
- Kiểm tra Telegram nhận được thông báo
- Kiểm tra Odoo: `crm.lead` / `purchase.order` / `hse.chemical.declaration` có record mới
- Kiểm tra `pubsub.event.log` trong Odoo: state = "processed"
- Kiểm tra webhook logs: `tail -f ~/.hermes/logs/gateway.log | grep "webhook"`
