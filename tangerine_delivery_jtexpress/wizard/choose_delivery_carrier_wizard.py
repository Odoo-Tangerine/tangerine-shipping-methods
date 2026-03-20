# -*- coding: utf-8 -*-
from odoo import fields, models, api
from ..settings.constants import settings


class ChooseDeliveryCarrierJTExpress(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    jtexpress_payment_type = fields.Selection(
        selection=settings.payment_type.value,
        string='Payment Type'
    )
    jtexpress_order_type = fields.Selection(
        selection=settings.order_type.value,
        string='Order Type'
    )
    jtexpress_service_type = fields.Selection(
        selection=settings.service_type.value,
        string='Service Type'
    )

    @api.onchange('carrier_id', 'total_weight')
    def _onchange_jtexpress_provider(self):
        res = super(ChooseDeliveryCarrierJTExpress, self)._onchange_carrier_id()
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.code.value:
                rec.jtexpress_payment_type = rec.carrier_id.default_jtexpress_payment_type
                rec.jtexpress_order_type = rec.carrier_id.default_jtexpress_order_type
                rec.jtexpress_service_type = rec.carrier_id.default_jtexpress_service_type
        return res

    def _get_delivery_rate(self):
        if self.carrier_id.delivery_type == settings.code.value:
            self = self.with_context(
                jtexpress_total_weight=self.total_weight,
                jtexpress_payment_type=self.jtexpress_payment_type or self.carrier_id.default_jtexpress_payment_type,
                jtexpress_service_type=self.jtexpress_service_type or self.carrier_id.default_jtexpress_service_type,
            )
        return super(ChooseDeliveryCarrierJTExpress, self)._get_delivery_rate()

    def button_confirm(self):
        return super(ChooseDeliveryCarrierJTExpress, self).button_confirm()
