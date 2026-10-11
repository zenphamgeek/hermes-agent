# -*- coding: utf-8 -*-
from odoo import models, fields


class HSEComplianceEvent(models.Model):
    _name = 'hse.compliance.event'
    _description = 'HSE Knowledge Compliance Event'

    name = fields.Char(string='Reference', required=True, default=lambda self: self.env['ir.sequence'].next_by_code('hse.compliance.event') or 'HSE-EVT')
    event_type = fields.Char(string='Event Type', required=True)
    event_payload = fields.Text(string='Payload JSON')
    received_date = fields.Datetime(string='Received At', default=fields.Datetime.now)
    state = fields.Selection([
        ('draft', 'New'),
        ('reviewed', 'Reviewed'),
        ('applied', 'Applied to Legal Register')
    ], string='Status', default='draft')
