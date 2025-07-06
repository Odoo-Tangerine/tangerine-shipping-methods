from odoo import fields, models
from ..settings.constants import settings


class CarrierTrackingRef(models.Model):
    _inherit = 'carrier.ref.order'

    ntl_service_type = fields.Selection(selection=settings.service_type.value, string='Service Type')
    ntl_payment_method = fields.Selection(selection=settings.payment_method.value, string='Payment Method')
    ntl_cargo_type = fields.Selection(selection=settings.cargo_type.value, string='Cargo Type')
