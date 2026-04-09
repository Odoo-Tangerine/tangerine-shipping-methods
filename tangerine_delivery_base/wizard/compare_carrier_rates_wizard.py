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
        """Fetch shipping rates from all eligible carriers using their default configs."""
        self.ensure_one()
        order = self.order_id

        if not order.partner_shipping_id:
            raise UserError(_('Please set a shipping address on the sale order.'))

        # Find all locally-integrated carriers
        carriers = self.env['delivery.carrier'].search([
            ('delivery_type', 'not in', ['fixed', 'base_on_rule']),
            ('is_locally_delivery', '=', True),
        ])

        lines = []
        for carrier in carriers:
            try:
                result = carrier.rate_shipment_with_defaults(order)
                lines.append((0, 0, {
                    'carrier_id': carrier.id,
                    'delivery_type': result.get('delivery_type', ''),
                    'price': result.get('price', 0.0),
                    'carrier_price': result.get('carrier_price', result.get('price', 0.0)),
                    'success': result.get('success', False),
                    'error_message': result.get('error_message') or '',
                    'warning_message': result.get('warning_message') or '',
                }))
            except Exception as e:
                _logger.warning('Failed to get rate from %s: %s', carrier.name, e)
                lines.append((0, 0, {
                    'carrier_id': carrier.id,
                    'delivery_type': carrier.delivery_type,
                    'price': 0.0,
                    'carrier_price': 0.0,
                    'success': False,
                    'error_message': str(e),
                }))

        self.write({
            'line_ids': [(5, 0, 0)] + lines,
            'is_loading': False,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Carrier Rate Comparison'),
            'res_model': 'compare.carrier.rates.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_select_carrier(self):
        """Select the chosen carrier and set the delivery line on the sale order."""
        self.ensure_one()
        line = self.line_ids.filtered(lambda l: l.is_selected)
        if not line:
            raise UserError(_('Please select a carrier.'))
        if len(line) > 1:
            raise UserError(_('Please select only one carrier.'))
        if not line.success:
            raise UserError(_('Cannot select a carrier with a failed rate quote.'))

        order = self.order_id
        carrier = line.carrier_id
        order.set_delivery_line(carrier, line.price)
        order.write({
            'carrier_id': carrier.id,
            'recompute_delivery_price': False,
        })

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
