from odoo import fields, models, api, _
from ..settings.constants import settings


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    viettelpost_order_payment = fields.Selection(selection=settings.order_payment.value, string='Payment Type')
    viettelpost_product_type = fields.Selection(selection=settings.product_type.value, string='Product Type')
    viettelpost_national_type = fields.Selection(selection=settings.national_type.value, string='Types of Shipments')
    viettelpost_service_request_domain = fields.Binary(default=[], store=False)
    viettelpost_service_id = fields.Many2one('viettelpost.service', string='Service')
    viettelpost_service_extend_id = fields.Many2one('viettelpost.service.extend', string='Service Extend')

    @api.onchange('carrier_id')
    def _onchange_viettelpost_provider(self):
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.code.value:
                rec.viettelpost_order_payment = rec.carrier_id.default_viettelpost_order_payment
                rec.viettelpost_product_type = rec.carrier_id.default_viettelpost_product_type
                rec.viettelpost_national_type = rec.carrier_id.default_viettelpost_national_type
                rec.viettelpost_service_id = rec.carrier_id.default_viettelpost_service_id
                rec.viettelpost_service_extend_id = rec.carrier_id.default_viettelpost_service_extend_id

    @api.onchange('viettelpost_order_payment')
    def _onchange_viettelpost_order_payment(self):
        for rec in self:
            if rec.viettelpost_order_payment and rec.delivery_type == settings.code.value:
                if rec.viettelpost_order_payment == settings.order_payment_no_collection.value:
                    rec.cash_on_delivery = False
                    rec.cash_on_delivery_amount = 0.0
                else:
                    rec.cash_on_delivery = True
                    rec.cash_on_delivery_amount = rec.sale_id.amount_total

    @api.onchange('viettelpost_service_id')
    def _onchange_viettelpost_service_id(self):
        for rec in self:
            if rec.viettelpost_service_id:
                rec.viettelpost_service_request_domain = [('service_id', '=', rec.viettelpost_service_id.id)]

    def viettelpost_print_order(self):
        self.ensure_one()
        if self.delivery_type == settings.code.value:
            if not self.carrier_id.default_viettelpost_paper_size:
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
                'url': self.carrier_id.viettelpost_print_order(
                    self.carrier_tracking_ref,
                    self.carrier_id.default_viettelpost_paper_size
                ),
                'close': True
            }
