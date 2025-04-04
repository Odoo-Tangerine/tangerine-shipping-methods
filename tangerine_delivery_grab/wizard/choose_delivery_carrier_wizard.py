import json
from odoo import fields, models, api
from ..settings.constants import settings


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    grab_service_type = fields.Selection(selection=settings.service_type.value, string='Service Type')
    grab_vehicle_type = fields.Selection(selection=settings.vehicle_type.value, string='Vehicle Type')

    @api.onchange('carrier_id')
    def _onchange_grab_provider(self):
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.grab_code.value:
                rec.grab_service_type = rec.carrier_id.default_grab_service_type
                rec.grab_vehicle_type = rec.carrier_id.default_grab_vehicle_type

    def _get_delivery_rate(self):
        if self.carrier_id.delivery_type == settings.grab_code.value:
            context = dict(self.env.context)
            context.update({
                'grab_service_type': self.grab_service_type or self.carrier_id.default_grab_service_type or settings.default_service_type.value,
                'grab_vehicle_type': self.grab_vehicle_type or self.carrier_id.default_grab_vehicle_type or settings.default_vehicle_type.value,
                'grab_cod': self.is_cod,
                'grab_cod_amount': self.cod_amount,
            })
            self.env.context = context
        return super(ChooseDeliveryCarrier, self)._get_delivery_rate()

    def button_confirm(self):
        if self.carrier_id.delivery_type == settings.grab_code.value:
            context = dict(self.env.context)
            context.update({'grab_quotation_data': json.dumps({
                'grab_service_type': self.grab_service_type,
                'grab_vehicle_type': self.grab_vehicle_type,
                'grab_cod': self.is_cod,
                'grab_cod_amount': self.cod_amount
            })})
            self.env.context = context
        return super(ChooseDeliveryCarrier, self).button_confirm()
