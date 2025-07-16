import json
from odoo import fields, models, api
from ..settings.constants import settings


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    ntl_service_type = fields.Selection(selection=settings.service_type.value, string='Service Type')
    ntl_payment_method = fields.Selection(selection=settings.payment_method.value, string='Payment Method')

    @api.onchange('carrier_id')
    def _onchange_nhat_tin_provider(self):
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.nhat_tin_code.value:
                rec.ntl_service_type = rec.carrier_id.default_ntl_service_type
                rec.ntl_payment_method = rec.carrier_id.default_ntl_payment_method

    def _get_delivery_rate(self):
        if self.carrier_id.delivery_type == settings.nhat_tin_code.value:
            context = dict(self.env.context)
            context.update({
                'ntl_service_type': self.ntl_service_type or self.carrier_id.default_ntl_service_type or settings.default_service_type.value,
                'ntl_payment_method': self.ntl_payment_method or self.carrier_id.default_ntl_payment_method or settings.default_payment_method.value,
                'ntl_cod': self.is_cod,
                'ntl_cod_amount': self.cod_amount,
                'ntl_cargo_value': self.order_id.amount_total,
            })
            self.env.context = context
        return super(ChooseDeliveryCarrier, self)._get_shipment_rate()

    def button_confirm(self):
        if self.carrier_id.delivery_type == settings.nhat_tin_code.value:
            context = dict(self.env.context)
            context.update({'ntl_quotation_data': json.dumps({
                'ntl_service_type': self.ntl_service_type,
                'ntl_payment_method': self.ntl_payment_method,
                'ntl_cod': self.is_cod,
                'ntl_cod_amount': self.cod_amount
            })})
            self.env.context = context
        return super().button_confirm()
