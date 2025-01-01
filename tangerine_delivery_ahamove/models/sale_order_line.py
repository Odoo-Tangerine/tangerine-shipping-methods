from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    ahamove_quotation_data = fields.Json(string='Ahamove Quotation Data')
