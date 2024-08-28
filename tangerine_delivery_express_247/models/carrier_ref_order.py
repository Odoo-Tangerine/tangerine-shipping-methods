from odoo import fields, models
from ..settings.constants import settings


class CarrierTrackingRef(models.Model):
    _inherit = 'carrier.ref.order'

    express_247_is_inspection_goods_allowed = fields.Boolean(string='Inspection Goods  Allowed', default=False)
    express_247_service_type_id = fields.Many2one(
        'service.type.247.express',
        string='Service Type'
    )
    express_247_special_service_type_ids = fields.Many2many(
        'special.service.type.247.express',
        string='Special Service Type'
    )

    express_247_product_type = fields.Selection(settings.product_type.value, string='Product Type')
