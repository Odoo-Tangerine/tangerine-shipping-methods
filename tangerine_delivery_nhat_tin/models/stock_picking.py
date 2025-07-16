from odoo import models, fields, api, _
from ..settings.constants import settings


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    ntl_service_type = fields.Selection(selection=settings.service_type.value, string='Service Type')
    ntl_payment_method = fields.Selection(selection=settings.payment_method.value, string='Payment Method')
    ntl_cargo_type = fields.Selection(selection=settings.cargo_type.value, string='Cargo Type')

    @api.onchange('carrier_id')
    def _onchange_nhat_tin_provider(self):
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.nhat_tin_code.value:
                rec.ntl_service_type = rec.carrier_id.default_ntl_service_type
                rec.ntl_payment_method = rec.carrier_id.default_ntl_payment_method
                rec.ntl_cargo_type = rec.carrier_id.default_ntl_cargo_type

    def nhat_tin_print_order(self):
        self.ensure_one()
        return self.carrier_id.nhat_tin_print_order(self.carrier_tracking_ref)