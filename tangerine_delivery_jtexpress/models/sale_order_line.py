# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    jtexpress_quotation_data = fields.Json(string='J&T Express Quotation Data')
