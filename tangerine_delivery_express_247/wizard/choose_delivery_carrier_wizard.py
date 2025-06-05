from odoo import fields, models, api, _
from ..settings.constants import settings


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    express_247_service_type_id = fields.Many2one('service.type.247.express', string='Service Type')

    @api.onchange('carrier_id', 'total_weight')
    def _onchange_express_247_provider(self):
        res = super(ChooseDeliveryCarrier, self)._onchange_carrier_id()
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.code.value:
                rec.express_247_service_type_id = rec.carrier_id.default_express_247_service_type_id
        return res

    def _get_delivery_rate(self):
        if self.carrier_id.delivery_type == settings.code.value:
            context = dict(self.env.context)
            context.update({
                'express_247_service_type': self.express_247_service_type_id.code or self.carrier_id.default_express_247_service_type_id.code or settings.default_service_type.value,
            })
            self.env.context = context
        return super(ChooseDeliveryCarrier, self)._get_delivery_rate()
