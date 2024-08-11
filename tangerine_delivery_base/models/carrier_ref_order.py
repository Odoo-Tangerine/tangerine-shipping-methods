from odoo import fields, models


class CarrierRefOrder(models.Model):
    _name = 'carrier.ref.order'
    _rec_name = 'carrier_tracking_ref'
    _order = 'create_date desc'
    _description = 'Carrier Ref Order'

    picking_id = fields.Many2one('stock.picking', string='Picking', required=True, readonly=True)
    sale_id = fields.Many2one(related='picking_id.sale_id', string='Sale Order')
    carrier_id = fields.Many2one(related='picking_id.carrier_id', string='Carrier', store=True)
    delivery_type = fields.Selection(related='carrier_id.delivery_type')
    currency_id = fields.Many2one(related='picking_id.currency_id')
    carrier_tracking_ref = fields.Char(related='picking_id.carrier_tracking_ref', string='Carrier Tracking Ref')
    remarks = fields.Char(related='picking_id.remarks', string='Remarks')
    cash_on_delivery = fields.Boolean(related='picking_id.cash_on_delivery', string='COD')
    cash_on_delivery_amount = fields.Monetary(related='picking_id.cash_on_delivery_amount', string='COD Money')
    schedule_order = fields.Boolean(related='picking_id.schedule_order', string='Schedule')
    schedule_pickup_time_from = fields.Datetime(
        related='picking_id.schedule_pickup_time_from',
        string='Pickup Time From'
    )
    schedule_pickup_time_to = fields.Datetime(
        related='picking_id.schedule_pickup_time_to',
        string='Pickup Time To'
    )
    delivery_charge = fields.Float(related='picking_id.carrier_price')

    driver_name = fields.Char(related='picking_id.driver_name', string='Driver Name')
    driver_phone = fields.Char(related='picking_id.driver_phone', string='Driver Phone')
    driver_license_plate = fields.Char(related='picking_id.driver_license_plate')
    promo_code = fields.Char(related='picking_id.promo_code', string='Promo Code')
    delivery_status_id = fields.Many2one(related='picking_id.delivery_status_id', string='Delivery Status')
    real_delivery_charge = fields.Monetary(currency_field='currency_id', string='Real Shipping Cost', readonly=True)
