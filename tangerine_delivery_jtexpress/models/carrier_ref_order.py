# -*- coding: utf-8 -*-
from odoo import fields, models
from ..settings.constants import settings


class CarrierRefOrderJTExpress(models.Model):
    _inherit = 'carrier.ref.order'

    jtexpress_goods_type = fields.Selection(
        selection=settings.goods_type.value,
        string='Goods Type'
    )
