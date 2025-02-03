from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_delivery_line_vals(self, carrier, price_unit):
        values = super(SaleOrder, self)._prepare_delivery_line_vals(carrier, price_unit)
        if self.env.context.get('viettelpost_quotation_data'):
            values.update({'viettelpost_quotation_data': self.env.context.get('viettelpost_quotation_data')})
        return values
