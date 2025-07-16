from odoo import models, fields, api
from ..settings.constants import settings


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    ahamove_service_id = fields.Many2one('ahamove.service', string='Service Type')
    ahamove_service_request_ids = fields.Many2many('ahamove.service.request', 'picking_request_rel',
                                                   'picking_id', 'request_id', string='Request Type')
    ahamove_service_request_domain = fields.Binary(default=[], store=False)
    ahamove_payment_method = fields.Selection(selection=settings.payment_method.value, string='Payment Method')
    ahamove_shared_link = fields.Char(string='Shared Link')

    @api.onchange('ahamove_service_id')
    def _onchange_ahamove_service_id(self):
        for rec in self:
            if rec.ahamove_service_id:
                rec.ahamove_service_request_domain = [('service_id', '=', rec.ahamove_service_id.id)]

    @api.onchange('carrier_id')
    def _onchange_ahamove_provider(self):
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.ahamove_code.value:
                rec.ahamove_service_id = rec.carrier_id.default_ahamove_service_id
                rec.ahamove_service_request_ids = rec.carrier_id.default_ahamove_service_request_ids
                rec.ahamove_payment_method = rec.carrier_id.default_ahamove_payment_method
