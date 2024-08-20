from odoo import fields, models
from ..settings.constants import settings


class CarrierTrackingRef(models.Model):
    _inherit = 'carrier.ref.order'

    ghtk_transport_type = fields.Selection(settings.transport_type.value, string='Transport Type')
    ghtk_service_type = fields.Selection(settings.service_type.value, string='Service Type')
    ghtk_special_service_type_ids = fields.Many2many('ghtk.special.service', string='Special Service Type')
    ghtk_payer_type = fields.Selection(settings.payer_type.value, string='Payer')
