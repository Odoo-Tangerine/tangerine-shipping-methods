from odoo import fields, models
from ..settings.constants import settings


class CarrierTrackingRef(models.Model):
    _inherit = 'carrier.ref.order'

    is_lalamove_goods_fragile = fields.Boolean(string='Goods Fragile', default=False)
    lalamove_service_id = fields.Many2one('lalamove.service', string='Service Type')
    lalamove_special_service_ids = fields.Many2many('lalamove.special.service', string='Special Request')
