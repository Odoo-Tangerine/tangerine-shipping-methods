# -*- coding: utf-8 -*-
from odoo import fields, models
from ..settings.constants import settings


class CarrierRefOrderJTExpress(models.Model):
    _inherit = 'carrier.ref.order'

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
