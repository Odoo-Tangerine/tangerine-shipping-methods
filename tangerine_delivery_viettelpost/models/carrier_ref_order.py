from odoo import fields, models
from ..settings.constants import settings


class CarrierTrackingRef(models.Model):
    _inherit = 'carrier.ref.order'

    viettelpost_order_payment = fields.Selection(selection=settings.order_payment.value, string='Payment Type')
    viettelpost_product_type = fields.Selection(selection=settings.product_type.value, string='Product Type')
    viettelpost_national_type = fields.Selection(selection=settings.national_type.value, string='Types of Shipments')
    viettelpost_service_id = fields.Many2one('viettelpost.service', string='Service')
    viettelpost_service_extend_id = fields.Many2one('viettelpost.service.extend', string='Service Extend')
