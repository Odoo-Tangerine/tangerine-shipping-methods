from odoo import fields, models, _
from odoo.exceptions import UserError


class PrintOrderWizard(models.TransientModel):
    _name = 'print.order.wizard'
    _description = 'Print Order Wizard'

    picking_id = fields.Many2one('stock.picking', required=True, string='Picking')
    delivery_type = fields.Selection(related='picking_id.delivery_type')
    carrier_tracking_ref = fields.Char(related='picking_id.carrier_tracking_ref', string='Carrier Tracking Ref')

    def print_order(self):
        if hasattr(self, f'{self.delivery_type}_print_order'):
            return {
                'type': 'ir.actions.act_url',
                'url': getattr(self, f'{self.delivery_type}_print_order')(),
                'close': True
            }
        else:
            raise UserError(_(f'The carrier {self.picking_id.carrier_id.name} not support feature print order'))

