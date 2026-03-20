# -*- coding: utf-8 -*-
from odoo import fields, models, api
from ..settings.constants import settings


class StockPicking(models.Model):
    _inherit = 'stock.picking'

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

    @api.onchange('carrier_id')
    def _onchange_jtexpress_provider(self):
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.code.value:
                rec.jtexpress_payment_type = rec.carrier_id.default_jtexpress_payment_type
                rec.jtexpress_order_type = rec.carrier_id.default_jtexpress_order_type
                rec.jtexpress_service_type = rec.carrier_id.default_jtexpress_service_type

    @api.onchange('jtexpress_payment_type')
    def _onchange_jtexpress_payment_type(self):
        for rec in self:
            if rec.jtexpress_payment_type and rec.delivery_type == settings.code.value:
                # paytype 1 = sender pays; COD is not related to paytype
                # COD is set separately via cash_on_delivery field
                pass
