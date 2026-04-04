# -*- coding: utf-8 -*-
from odoo import models

from ..settings.constants import settings


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_delivery_line_vals(self, carrier, price_unit):
        values = super()._prepare_delivery_line_vals(carrier, price_unit)
        if carrier.delivery_type == settings.code.value and self.env.context.get('jtexpress_quotation_data'):
            values['jtexpress_quotation_data'] = self.env.context['jtexpress_quotation_data']
        return values
