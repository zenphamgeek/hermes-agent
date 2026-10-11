# -*- coding: utf-8 -*-
from odoo import fields, models


class HSTariff(models.Model):
    _name = 'hs.tariff'
    _description = 'Vietnam HS Tariff Schedule & Duty Rates'
    _order = 'hs_code asc'

    hs_code = fields.Char(string='HS Code (8-digit)', required=True, index=True)
    description = fields.Text(string='Description (Vietnamese / English)', required=True)
    import_duty_rate = fields.Float(string='Preferential Import Duty Rate (%)', digits=(5, 2), default=0.0)
    vat_rate = fields.Float(string='VAT Rate (%)', digits=(5, 2), default=10.0)
    specialized_management_notes = fields.Text(string='Specialized Regulations / Policy Notes')
    legal_basis = fields.Char(string='Legal Basis / Circular Reference')
    active = fields.Boolean(string='Active', default=True, index=True)
