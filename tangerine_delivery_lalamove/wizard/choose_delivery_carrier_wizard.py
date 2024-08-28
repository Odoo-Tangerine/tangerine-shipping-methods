from odoo import fields, models, api
from ..settings.constants import settings


class ChooseDeliveryCarrierLalamove(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    lalamove_service_id = fields.Many2one('lalamove.service', string='Vehicle Type')
    lalamove_special_service_domain = fields.Binary(default=[], store=False)
    lalamove_special_service_ids = fields.Many2many(
        'lalamove.special.service',
        'lalamove_estimate_request_rel',
        'choose_id',
        'special_id',
        string='Service Type'
    )
    lalamove_quotation_data = fields.Json(string='Lalamove Quotation Data')

    @api.onchange('carrier_id', 'total_weight')
    def _onchange_lalamove_provider(self):
        res = super(ChooseDeliveryCarrierLalamove, self)._onchange_carrier_id()
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.lalamove_code.value:
                rec.lalamove_service_id = rec.carrier_id.default_lalamove_service_id
                rec.lalamove_special_service_ids = rec.carrier_id.default_lalamove_special_service_ids
                rec.lalamove_special_service_domain = [('service_id', '=', rec.carrier_id.default_lalamove_service_id.id)]
        return res

    @api.onchange('lalamove_service_id')
    def _onchange_lalamove_service_id(self):
        for rec in self:
            if rec.lalamove_service_id:
                rec.lalamove_special_service_domain = [('service_id', '=', rec.lalamove_service_id.id)]

    def _get_shipment_rate(self):
        if self.carrier_id.delivery_type == settings.lalamove_code.value:
            context = dict(self.env.context)
            context.update({
                'llm_service': self.lalamove_service_id.code,
                'llm_special_service': [spec.code for spec in self.lalamove_special_service_ids],
            })
            self.env.context = context
        result = super(ChooseDeliveryCarrierLalamove, self)._get_shipment_rate()
        if self.env.context.get('llm_quotation_data'):
            self.write({'lalamove_quotation_data': self.env.context.get('llm_quotation_data')})
        return result

    def button_confirm(self):
        if self.lalamove_quotation_data and self.carrier_id.delivery_type == settings.lalamove_code.value:
            context = dict(self.env.context)
            context.update({'llm_quotation_data': self.lalamove_quotation_data})
            self.env.context = context
        self.order_id.set_delivery_line(self.carrier_id, self.delivery_price)
        self.order_id.write({
            'recompute_delivery_price': False,
            'delivery_message': self.delivery_message,
        })
