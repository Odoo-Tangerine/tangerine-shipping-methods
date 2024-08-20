from odoo import fields, models
from ..settings.constants import settings


class CarrierTrackingRef(models.Model):
    _inherit = 'carrier.ref.order'

    grab_service_type = fields.Selection(selection=settings.service_type.value, string='Service Type')
    grab_vehicle_type = fields.Selection(selection=settings.vehicle_type.value, string='Vehicle Type')
    grab_payment_method = fields.Selection(selection=settings.payment_method.value, string='Payment Method')
    grab_payer = fields.Selection(selection=settings.payer.value, string='Payer')
    grab_cod_type = fields.Selection(
        selection=settings.cod_type.value,
        string='COD Type',
        default=settings.default_cod_type.value
    )
    grab_high_value = fields.Boolean(string='Order High Value', default=False)
