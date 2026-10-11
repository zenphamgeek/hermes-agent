# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hs_code_customs = fields.Char(string='Customs HS Code (8-digit)', index=True, help='Authoritative 8-digit Vietnam HS Code')
    import_duty_rate = fields.Float(string='Preferential Import Duty Rate (%)', digits=(5, 2))
    vat_rate = fields.Float(string='VAT Rate (%)', digits=(5, 2))
    specialized_management_notes = fields.Text(string='Specialized Management / Quản Lý Chuyên Ngành')
    hs_last_synced = fields.Datetime(string='HS Last Synchronized')
