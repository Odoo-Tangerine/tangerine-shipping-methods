from odoo import models, fields, api, _
from ..settings.constants import settings


class StockPicking(models.Model):
    _inherit = 'stock.picking'

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
    grab_tracking_link = fields.Char(string='Grab Tracking Link')

    @api.onchange('carrier_id')
    def _onchange_grab_provider(self):
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.grab_code.value:
                rec.grab_service_type = rec.carrier_id.default_grab_service_type
                rec.grab_vehicle_type = rec.carrier_id.default_grab_vehicle_type
                rec.grab_payment_method = rec.carrier_id.default_grab_payment_method
                rec.grab_payer = rec.carrier_id.default_grab_payer
