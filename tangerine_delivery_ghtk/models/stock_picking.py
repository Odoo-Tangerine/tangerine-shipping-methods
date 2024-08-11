from odoo import models, fields, api, _
from ..settings.constants import settings


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    ghtk_pick_shift = fields.Selection(settings.pick_shift.value, string='Pick Shift')
    ghtk_deliver_shift = fields.Selection(settings.deliver_shift.value, string='Deliver Shift')
    ghtk_transport_type = fields.Selection(settings.transport_type.value, string='Transport Type')
    ghtk_service_type = fields.Selection(settings.service_type.value, string='Service Type')
    ghtk_special_service_type_ids = fields.Many2many('ghtk.special.service', string='Special Service Type')
    ghtk_payer_type = fields.Selection(settings.payer_type.value, string='Payer')

    @api.onchange('carrier_id')
    def _onchange_ghtk_provider(self):
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.ghtk_code.value:
                rec.ghtk_pick_shift = rec.carrier_id.default_ghtk_pick_shift
                rec.ghtk_transport_type = rec.carrier_id.default_ghtk_transport_type
                rec.ghtk_service_type = rec.carrier_id.default_ghtk_service_type
                rec.ghtk_special_service_type_ids = rec.carrier_id.default_ghtk_special_service_type_ids
                rec.ghtk_payer_type = rec.carrier_id.default_ghtk_payer_type

    def ghtk_print_order(self):
        self.ensure_one()
        if self.delivery_type == settings.ghtk_code.value:
            if not self.carrier_id.default_ghtk_print_layout or not self.carrier_id.default_ghtk_paper_size:
                return {
                    'name': _('Print Order Wizard'),
                    'view_mode': 'form',
                    'res_model': 'print.order.wizard',
                    'view_id': self.env.ref('tangerine_delivery_base.print_order_wizard_form_view').id,
                    'type': 'ir.actions.act_window',
                    'context': {
                        'default_picking_id': self.id
                    },
                    'target': 'new'
                }
            return {
                'type': 'ir.actions.act_url',
                'url': self.carrier_id.ghtk_print_order(
                    self,
                    self.carrier_id.default_ghtk_print_layout,
                    self.carrier_id.default_ghtk_paper_size
                ),
                'close': True
            }