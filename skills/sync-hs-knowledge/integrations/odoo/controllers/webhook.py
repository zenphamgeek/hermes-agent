# -*- coding: utf-8 -*-
import hashlib
import hmac
import json
import logging
import time
from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class HermesHSWebhookController(http.Controller):

    @http.route('/hermes/webhooks/hs-events', type='http', auth='public', methods=['POST'], csrf=False)
    def receive_hs_event(self, **kwargs):
        """
        Receives and processes signed HS knowledge events from Hermes Agent Webhook Hub.
        """
        req = request.httprequest
        secret = request.env['ir.config_parameter'].sudo().get_param('hermes.hs_webhook_secret', '')
        received_sig = req.headers.get('X-HS-Signature-256')
        received_ts = req.headers.get('X-HS-Timestamp')
        raw_body = req.get_data()

        # 1. Anti-replay verification (300s window) if timestamp provided
        if received_ts:
            try:
                ts_int = int(received_ts)
                now_int = int(time.time())
                if abs(now_int - ts_int) > 300:
                    _logger.warning("Rejected Hermes Webhook due to timestamp drift: %s (now=%s)", ts_int, now_int)
                    return request.make_json_response({'status': 'error', 'message': 'Timestamp outside valid window'}, status=400)
            except (ValueError, TypeError):
                pass

        # 2. Verify HMAC-SHA256 signature if secret configured
        if secret and received_sig:
            expected_sig = "sha256=" + hmac.new(secret.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected_sig, received_sig):
                _logger.warning("Invalid HMAC signature received for Hermes HS Webhook")
                return request.make_json_response({'status': 'error', 'message': 'Invalid signature'}, status=401)

        try:
            payload = json.loads(raw_body.decode('utf-8'))
        except Exception as e:
            return request.make_json_response({'status': 'error', 'message': f'Invalid JSON payload: {e}'}, status=400)

        event_type = payload.get('event_type')
        data = payload.get('data', {})
        event_id = payload.get('event_id')
        _logger.info("Processing Hermes HS event: %s (id=%s)", event_type, event_id)

        env = request.env(su=True)

        # 3. Process specific event types
        if event_type == 'hs.ruling.published':
            ruling_model = env['hs.customs.ruling']
            ruling_num = data.get('document_id') or data.get('ruling_number')
            if ruling_num:
                existing = ruling_model.search([('ruling_number', '=', ruling_num)], limit=1)
                vals = {
                    'ruling_number': ruling_num,
                    'hs_code': data.get('hs_code', ''),
                    'product_description': data.get('product_name') or data.get('product_description', ''),
                    'raw_text_summary': data.get('analysis', ''),
                    'active': True,
                }
                if existing:
                    existing.write(vals)
                else:
                    ruling_model.create(vals)

        elif event_type == 'hs.tariff.changed':
            tariff_model = env['hs.tariff']
            hs_code = data.get('hs_code')
            if hs_code:
                existing = tariff_model.search([('hs_code', '=', hs_code)], limit=1)
                vals = {
                    'hs_code': hs_code,
                    'description': data.get('description', ''),
                    'import_duty_rate': data.get('mfn_rate', 0.0),
                    'vat_rate': data.get('vat_rate', 0.0),
                }
                if existing:
                    existing.write(vals)
                else:
                    tariff_model.create(vals)

        return request.make_json_response({'status': 'success', 'event_id': event_id})
