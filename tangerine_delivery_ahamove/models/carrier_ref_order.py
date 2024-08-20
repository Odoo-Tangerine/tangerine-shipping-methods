from odoo import fields, models
from ..settings.constants import settings


class CarrierTrackingRef(models.Model):
    _inherit = 'carrier.ref.order'

    ahamove_service_id = fields.Many2one('ahamove.service', string='Service Type')
    ahamove_service_request_ids = fields.Many2many('ahamove.service.request', string='Request Type')
    ahamove_payment_method = fields.Selection(selection=settings.payment_method.value, string='Payment Method')
