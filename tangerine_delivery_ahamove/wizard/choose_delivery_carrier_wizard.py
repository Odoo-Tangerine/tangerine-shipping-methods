import json
import logging
from odoo import fields, models, api
from ..settings.constants import settings

_logger = logging.getLogger(__name__)


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    ahamove_service_id = fields.Many2one('ahamove.service', string='Service')
    ahamove_service_request_domain = fields.Binary(default=[], store=False)
    ahamove_service_request_ids = fields.Many2many(
        'ahamove.service.request',
        'estimate_request_rel',
        'choose_id',
        'request_id',
        string='Request Type'
    )
    promo_code = fields.Char(string='Promotion Code')

    @api.onchange('carrier_id', 'total_weight')
    def _onchange_ahamove_provider(self):
        res = super(ChooseDeliveryCarrier, self)._onchange_carrier_id()
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.ahamove_code.value:
                rec.ahamove_service_id = rec.carrier_id.default_ahamove_service_id
                rec.ahamove_service_request_ids = rec.carrier_id.default_ahamove_service_request_ids
        return res

    @api.onchange('ahamove_service_id')
    def _onchange_ahamove_service_id(self):
        for rec in self:
            if rec.ahamove_service_id:
                rec.ahamove_service_request_domain = [('service_id', '=', rec.ahamove_service_id.id)]

    def _get_delivery_rate(self):
        if self.carrier_id.delivery_type == settings.ahamove_code.value:
            context = dict(self.env.context)
            context.update({
                'ahamove_service': self.ahamove_service_id.code,
                'ahamove_service_request_ids': self.ahamove_service_request_ids,
                'promo_code': self.promo_code
            })
            self.env.context = context
        return super(ChooseDeliveryCarrier, self)._get_shipment_rate()

    def button_confirm(self):
        if self.carrier_id.delivery_type == settings.ahamove_code.value:
            context = dict(self.env.context)
            context.update({'ahamove_quotation_data': json.dumps({
                'ahamove_service_id': self.ahamove_service_id.id,
                'ahamove_service_request_ids': self.ahamove_service_request_ids.ids,
                'promo_code': self.promo_code,
                'ahamove_cod': self.is_cod,
                'ahamove_cod_amount': self.cod_amount
            })})
            self.env.context = context
            _logger.debug('context', context)
        return super().button_confirm()