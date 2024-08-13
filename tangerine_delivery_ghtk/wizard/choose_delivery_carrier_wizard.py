from odoo import fields, models, api
from ..settings.constants import settings


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    ghtk_transport_type = fields.Selection(settings.transport_type.value, string='Transport Type')
    ghtk_service_type = fields.Selection(settings.service_type.value, string='Service Type')
    ghtk_special_service_type_ids = fields.Many2many('ghtk.special.service', string='Special Service Type')

    @api.onchange('carrier_id', 'total_weight')
    def _onchange_ghtk_provider(self):
        res = super(ChooseDeliveryCarrier, self)._onchange_carrier_id()
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.ghtk_code.value:
                rec.ghtk_transport_type = rec.carrier_id.default_ghtk_transport_type
                rec.ghtk_service_type = rec.carrier_id.default_ghtk_service_type
                rec.ghtk_special_service_type_ids = rec.carrier_id.default_ghtk_special_service_type_ids
        return res

    def _get_shipment_rate(self):
        if self.carrier_id.delivery_type == settings.ghtk_code.value:
            context = dict(self.env.context)
            context.update({
                'ghtk_transport_type': self.ghtk_transport_type,
                'ghtk_service_type': self.ghtk_service_type,
                'ghtk_special_service_type': [int(rec.code) for rec in self.ghtk_special_service_type_ids]
            })
            self.env.context = context
        return super(ChooseDeliveryCarrier, self)._get_shipment_rate()
