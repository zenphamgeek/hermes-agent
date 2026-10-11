# -*- coding: utf-8 -*-
from odoo import models, fields

class HSCustomsRuling(models.Model):
    _name = 'hs.customs.ruling'
    _description = 'Vietnam Customs Advance Classification Ruling'
    _order = 'issue_date desc, id desc'

    ruling_number = fields.Char(string='Ruling Number / Số Thông Báo', required=True, index=True)
    issuing_authority = fields.Char(string='Issuing Authority / Cơ Quan Ban Hành', default='Tổng cục Hải quan')
    issue_date = fields.Date(string='Issue Date / Ngày Ban Hành')
    expiry_date = fields.Date(string='Expiry Date / Ngày Hết Hạn')
    hs_code = fields.Char(string='HS Code Kết Luận', required=True, index=True)
    commercial_name = fields.Char(string='Commercial Name / Tên Thương Mại')
    technical_description = fields.Text(string='Technical Description / Mô Tả Kỹ Thuật')
    classification_rationale = fields.Text(string='Classification Rationale / Căn Cứ Phân Loại')
    source_url = fields.Char(string='Source URL')
    artifact_sha256 = fields.Char(string='Artifact SHA-256')
    status = fields.Selection([
        ('active', 'Active / Có Hiệu Lực'),
        ('revoked', 'Revoked / Bị Hủy Bỏ'),
        ('expired', 'Expired / Hết Hiệu Lực')
    ], string='Status', default='active', index=True)
