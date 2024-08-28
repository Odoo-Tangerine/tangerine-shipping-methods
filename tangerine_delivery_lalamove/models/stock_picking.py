from odoo import fields, models, api
from ..settings.constants import settings


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_lalamove_goods_fragile = fields.Boolean(string='Goods Fragile', default=False)
    lalamove_service_id = fields.Many2one('lalamove.service', string='Service Type')
    lalamove_special_service_domain = fields.Binary(default=[], store=False)
    lalamove_special_service_ids = fields.Many2many(
        'lalamove.special.service',
        'lalamove_picking_special_rel',
        'picking_id',
        'special_id',
        string='Special Request'
    )
    lalamove_tracking_link = fields.Char(string='Tracking link')
    lalamove_got_quotation = fields.Boolean(compute='_lalamove_compute_got_quotation')

    def _lalamove_compute_got_quotation(self):
        for rec in self:
            rec.lalamove_got_quotation = bool(rec.sale_id.order_line.filtered(lambda l: l.lalamove_quotation_data and l.is_delivery))

    @api.onchange('lalamove_service_id')
    def _onchange_lalamove_service_id(self):
        for rec in self:
            if rec.lalamove_service_id:
                rec.lalamove_special_service_domain = [('service_id', '=', rec.lalamove_service_id.id)]

    @api.onchange('carrier_id')
    def _onchange_lalamove_provider(self):
        for rec in self:
            if rec.carrier_id and rec.carrier_id.delivery_type == settings.lalamove_code.value:
                rec.lalamove_service_id = rec.carrier_id.default_lalamove_service_id
                rec.lalamove_special_service_ids = rec.carrier_id.default_lalamove_special_service_ids
                rec.lalamove_special_service_domain = [('service_id', '=', rec.carrier_id.default_lalamove_service_id.id)]
