from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    viettelpost_quotation_data = fields.Json(string='Viettelpost Quotation Data')
