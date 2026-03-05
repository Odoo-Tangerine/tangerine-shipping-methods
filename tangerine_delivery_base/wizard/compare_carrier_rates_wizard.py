import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class CompareCarrierRatesWizard(models.TransientModel):
    _name = 'compare.carrier.rates.wizard'
    _description = 'Compare Carrier Rates'
    order_id = fields.Many2one('sale.order', string='Sale Order', required=True, readonly=True)
    line_ids = fields.One2many('compare.carrier.rates.wizard.line', 'wizard_id', string='Rate Quotes')
    is_loading = fields.Boolean(default=True)

    def action_fetch_rates(self):
        self.ensure_one()
        OOOOOO0OOO00O0OOO = self.order_id
        if not OOOOOO0OOO00O0OOO.partner_shipping_id:
            raise UserError(_('Please set a shipping address on the sale order.'))
        OO0O0OO000OOO0O0O = self.env['delivery.carrier'].search([('delivery_type', 'not in', ['fixed', 'base_on_rule']), ('is_locally_delivery', '=', True)])
        OOO0OO0OO00OOO0OO = []
        for OO000O00OO00O0000 in OO0O0OO000OOO0O0O:
            try:
                OO0O000000OOO0O00 = OO000O00OO00O0000.rate_shipment_with_defaults(OOOOOO0OOO00O0OOO)
                OOO0OO0OO00OOO0OO.append((0, 0, {'carrier_id': OO000O00OO00O0000.id, 'delivery_type': OO0O000000OOO0O00.get('delivery_type', ''), 'price': OO0O000000OOO0O00.get('price', 0.0), 'carrier_price': OO0O000000OOO0O00.get('carrier_price', OO0O000000OOO0O00.get('price', 0.0)), 'success': OO0O000000OOO0O00.get('success', False), 'error_message': OO0O000000OOO0O00.get('error_message') or '', 'warning_message': OO0O000000OOO0O00.get('warning_message') or ''}))
            except Exception as OO00O00O0OOOO0O0O:
                _logger.warning('Failed to get rate from %s: %s', OO000O00OO00O0000.name, OO00O00O0OOOO0O0O)
                OOO0OO0OO00OOO0OO.append((0, 0, {'carrier_id': OO000O00OO00O0000.id, 'delivery_type': OO000O00OO00O0000.delivery_type, 'price': 0.0, 'carrier_price': 0.0, 'success': False, 'error_message': str(OO00O00O0OOOO0O0O)}))
        self.write({'line_ids': [(5, 0, 0)] + OOO0OO0OO00OOO0OO, 'is_loading': False})
        return {'type': 'ir.actions.act_window', 'name': _('Carrier Rate Comparison'), 'res_model': 'compare.carrier.rates.wizard', 'res_id': self.id, 'view_mode': 'form', 'target': 'new'}

    def action_select_carrier(self):
        self.ensure_one()
        O00OOO00OOOO0O0O0 = self.line_ids.filtered(lambda l: l.is_selected)
        if not O00OOO00OOOO0O0O0:
            raise UserError(_('Please select a carrier.'))
        if len(O00OOO00OOOO0O0O0) > 1:
            raise UserError(_('Please select only one carrier.'))
        if not O00OOO00OOOO0O0O0.success:
            raise UserError(_('Cannot select a carrier with a failed rate quote.'))
        O00O0O00000OO0000 = self.order_id
        O0OOOOOOOOO00000O = O00OOO00OOOO0O0O0.carrier_id
        O00O0O00000OO0000.set_delivery_line(O0OOOOOOOOO00000O, O00OOO00OOOO0O0O0.price)
        O00O0O00000OO0000.write({'carrier_id': O0OOOOOOOOO00000O.id, 'recompute_delivery_price': False})
        return {'type': 'ir.actions.act_window_close'}

class CompareCarrierRatesWizardLine(models.TransientModel):
    _name = 'compare.carrier.rates.wizard.line'
    _description = 'Carrier Rate Line'
    _order = 'success desc, price asc'
    wizard_id = fields.Many2one('compare.carrier.rates.wizard', ondelete='cascade')
    carrier_id = fields.Many2one('delivery.carrier', string='Carrier', readonly=True)
    carrier_image = fields.Binary(related='carrier_id.image', string='Logo')
    delivery_type = fields.Char(string='Type', readonly=True)
    price = fields.Float(string='Price', digits='Product Price', readonly=True)
    carrier_price = fields.Float(string='Carrier Price', digits='Product Price', readonly=True)
    success = fields.Boolean(string='Available', readonly=True)
    error_message = fields.Char(string='Error', readonly=True)
    warning_message = fields.Char(string='Warning', readonly=True)
    is_selected = fields.Boolean(string='Select', default=False)
    currency_id = fields.Many2one(related='wizard_id.order_id.currency_id')