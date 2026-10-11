# Insilos Enterprise HS Knowledge Sync Connector

This directory documents the integration connector for **Insilos 19 Enterprise (Hard-Fork)** instances connecting to the Hermes HS Knowledge Sync Engine (`sync-hs-knowledge`).

The module source code resides in the Insilos core repository at:
`/home/zen/insilos_ee/insilos/apps/insilos_hs_sync`

## Key Capabilities

1. **Inbound Webhook Hub Receiver (`/insilos/webhooks/hs-events`)**:
   - Cryptographic HMAC-SHA256 verification (`X-HS-Signature-256`).
   - Anti-Replay Protection via `X-HS-Timestamp`.
   - Event processing for `hs.ruling.published`, `hs.tariff.changed`, `hs.legal.gazette`.
2. **Authoritative Entities in Insilos**:
   - `is.customs.ruling`: Vietnam Customs Advance Classification Rulings (Tổng cục Hải quan) with artifact SHA-256 provenance.
   - `is.hs.tariff`: Authoritative 8-digit Vietnam HS Code tariff schedule, preferential import duty rates, VAT, and specialized regulatory notes.
   - `is.hs.sync.log`: Complete audit trail of inbound webhooks and outbound REST queries.
   - `product.template`: Automatic tariff synchronization and smart lookup buttons.
3. **Outbound REST API Client**:
   - Direct integration with Hermes FastAPI endpoints (`/v1/hs/search`, `/v1/hs/classify`, `/v1/rulings/search`, `/v1/tariff/schedule`).

## Quick Setup

1. **Install Module in Insilos**:
   ```bash
   python3 tools/with_local_credentials.py --solo-dev-db -- ./insilos/insilos-bin -c insilos.conf -i insilos_hs_sync
   ```

2. **Register Webhook Subscriber in Hermes**:
   ```bash
   hs-sync webhook add insilos-prod "https://your-insilos-domain.com/insilos/webhooks/hs-events" \
     --events "hs.ruling.published,hs.tariff.changed" \
     --secret "your_shared_hmac_secret"
   ```
