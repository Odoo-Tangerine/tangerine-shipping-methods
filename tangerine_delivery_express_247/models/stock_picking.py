from odoo import fields, models, api, _
from ..settings.constants import settings


class StockPicking(models.Model):
    _inherit = 'stock.picking'

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

    @api.onchange('carrier_id')
    def _onchange_express_247_provider(self):
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.code.value:
                rec.express_247_service_type_id = rec.carrier_id.default_express_247_service_type_id
                rec.express_247_special_service_type_ids = rec.carrier_id.default_express_247_special_service_type_ids
                rec.express_247_product_type = rec.carrier_id.default_express_247_product_type
