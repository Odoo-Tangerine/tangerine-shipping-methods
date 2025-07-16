from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    ntl_quotation_data = fields.Json(string='Nhat Tin Logistics Quotation Data')
