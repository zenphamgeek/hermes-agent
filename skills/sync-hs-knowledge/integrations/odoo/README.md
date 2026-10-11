# Hermes HS Knowledge Sync Odoo Connector

This module enables any **Odoo 18 / 19 (Community & Enterprise)** instance to receive real-time customs classification rulings, HS codes, and tariff rate updates from the Hermes Agent Webhook Hub.

## Features

- **Automated HS Code Cataloging**: Keeps `product.template` synchronized with official 8-digit Vietnam HS codes and preferential import duty rates.
- **Customs Rulings Vault**: Stores official General Department of Customs (`Tổng cục Hải quan`) advance classification rulings (`hs.customs.ruling`) with direct legal basis and artifact SHA-256 provenance.
- **HMAC-SHA256 Security**: Rejects tampered or unauthenticated payloads using constant-time cryptographic verification.

## Setup in 2 Steps

1. **Install Module in Odoo**:
   Copy this directory to your Odoo custom addons directory (`addons/hermes_hs_sync`) and update your apps list.
2. **Register Webhook in Hermes**:
   ```bash
   hs-sync webhook add odoo-instance "https://your-odoo-domain.com/hermes/webhooks/hs-events" \
     --events "hs.ruling.published,hs.tariff.changed" \
     --secret "your_secret_key_here"
   ```
