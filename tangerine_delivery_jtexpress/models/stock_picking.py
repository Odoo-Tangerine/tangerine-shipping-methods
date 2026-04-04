# -*- coding: utf-8 -*-
from odoo import fields, models, api
from ..settings.constants import settings


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    jtexpress_goods_type = fields.Selection(
        selection=settings.goods_type.value,
        string='Goods Type'
    )

    @api.onchange('carrier_id')
    def _onchange_jtexpress_provider(self):
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.code.value:
                rec.jtexpress_goods_type = rec.carrier_id.default_jtexpress_goods_type
