# -*- coding: utf-8 -*-
import hmac
import hashlib
import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

HSE_WEBHOOK_SECRET = "sec_hse_2026"


class HSEWebhookController(http.Controller):

    @http.route('/webhooks/hse-events', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_hse_event(self, **kwargs):
        payload_bytes = request.httprequest.get_data()
        signature = request.httprequest.headers.get('X-HSE-Signature', '')
        event_type = request.httprequest.headers.get('X-HSE-Event', '')

        # Verify HMAC-SHA256 signature
        expected_sig = "sha256=" + hmac.new(
            HSE_WEBHOOK_SECRET.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            _logger.warning("Invalid HSE webhook HMAC signature received.")
            return {'status': 'error', 'message': 'Invalid signature'}

        try:
            data = json.loads(payload_bytes.decode('utf-8'))
            _logger.info(f"Successfully received HSE event: {event_type}")

            # Store in Odoo compliance model
            request.env['hse.compliance.event'].sudo().create({
                'event_type': event_type,
                'event_payload': json.dumps(data),
                'received_date': http.fields.Datetime.now()
            })

            return {'status': 'success', 'event_type': event_type}
        except Exception as e:
            _logger.error(f"Error processing HSE webhook: {str(e)}")
            return {'status': 'error', 'message': str(e)}
