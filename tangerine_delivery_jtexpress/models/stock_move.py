# -*- coding: utf-8 -*-
from odoo import models

from ..settings.constants import settings


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()
        order = self.sale_line_id.order_id
        if not order or order.carrier_id.delivery_type != settings.code.value:
            return vals

        delivery_line_ids = order.order_line.filtered('is_delivery')
        if not delivery_line_ids:
            return vals

        data = delivery_line_ids[-1].jtexpress_quotation_data or {}
        if not data:
            return vals

        vals.update({
            'jtexpress_goods_type': data.get('jtexpress_goods_type'),
            'cash_on_delivery': data.get('jtexpress_cod'),
            'cash_on_delivery_amount': data.get('jtexpress_cod_amount'),
        })
        return vals
