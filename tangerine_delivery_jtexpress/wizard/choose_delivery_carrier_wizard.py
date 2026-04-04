# -*- coding: utf-8 -*-
from odoo import api, fields, models

from ..settings.constants import settings


class ChooseDeliveryCarrierJTExpress(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    jtexpress_goods_type = fields.Selection(
        selection=settings.goods_type.value,
        string='Goods Type'
    )

    @api.onchange('carrier_id', 'total_weight')
    def _onchange_jtexpress_provider(self):
        res = super(ChooseDeliveryCarrierJTExpress, self)._onchange_carrier_id()
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.code.value:
                rec.jtexpress_goods_type = rec.carrier_id.default_jtexpress_goods_type
        return res

    @api.onchange('is_cod')
    def _onchange_jtexpress_cod(self):
        for rec in self:
            if rec.delivery_type != settings.code.value:
                continue
            rec.cod_amount = rec.order_id.amount_total if rec.is_cod else 0.0

    def _get_delivery_rate(self):
        if self.carrier_id.delivery_type == settings.code.value:
            self = self.with_context(
                jtexpress_total_weight=self.total_weight,
                jtexpress_cod_amount=self.cod_amount,
                jtexpress_goods_type=self.jtexpress_goods_type,
            )
        return super(ChooseDeliveryCarrierJTExpress, self)._get_delivery_rate()

    def button_confirm(self):
        if self.carrier_id.delivery_type == settings.code.value:
            self = self.with_context(jtexpress_quotation_data={
                'jtexpress_goods_type': self.jtexpress_goods_type or self.carrier_id.default_jtexpress_goods_type,
                'jtexpress_cod': self.is_cod,
                'jtexpress_cod_amount': self.cod_amount,
            })
        return super(ChooseDeliveryCarrierJTExpress, self).button_confirm()
