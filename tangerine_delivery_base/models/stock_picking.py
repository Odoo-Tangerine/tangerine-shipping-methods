from odoo import fields, models, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    is_locally_delivery = fields.Boolean(related='carrier_id.is_locally_delivery')
    is_support_feature_print_order = fields.Boolean(related='carrier_id.is_support_feature_print_order')
    remarks = fields.Char(string='Remarks')
    cash_on_delivery = fields.Boolean(string='COD', default=False)
    cash_on_delivery_amount = fields.Monetary(string='COD Money')
    schedule_order = fields.Boolean(string='Schedule', default=False)
    schedule_pickup_time_from = fields.Datetime(string='Pickup Time From', default=fields.Datetime.now)
    schedule_pickup_time_to = fields.Datetime(string='Pickup Time To')

    deliver_order_date = fields.Datetime(string='Deliver Order Date')
    promo_code = fields.Char(string='Promo Code')
    delivery_status_id = fields.Many2one('delivery.status', string='Delivery Status', readonly=True)
    delivery_status_code = fields.Char(related='delivery_status_id.code')

    @api.onchange('cash_on_delivery')
    def _on_change_cash_on_delivery(self):
        for rec in self:
            if rec.cash_on_delivery:
                rec.cash_on_delivery_amount = rec.sale_id.amount_total
            else:
                rec.cash_on_delivery_amount = 0.0

    def action_print_order(self):
        self.ensure_one()
        if self.carrier_id.is_support_feature_print_order and hasattr(self, f'{self.delivery_type}_print_order'):
            return getattr(self, f'{self.delivery_type}_print_order')()
        else:
            raise UserError(_(f'The carrier {self.carrier_id.name} not support future print order'))


