from odoo import fields, models


class CarrierRefOrder(models.Model):
    _name = 'carrier.ref.order'
    _rec_name = 'carrier_tracking_ref'
    _order = 'create_date desc'
    _description = 'Carrier Ref Order'

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    picking_id = fields.Many2one('stock.picking', string='Picking', required=True)
    sale_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    carrier_id = fields.Many2one('delivery.carrier', string='Carrier', required=True)
    delivery_type = fields.Selection(related='carrier_id.delivery_type')
    carrier_tracking_ref = fields.Char(string='Carrier Tracking Ref', required=True)
    remarks = fields.Char(related='picking_id.remarks', string='Remarks')
    cash_on_delivery = fields.Boolean(string='COD')
    cash_on_delivery_amount = fields.Monetary(string='COD Money')
    schedule_order = fields.Boolean(string='Schedule')
    schedule_pickup_time_from = fields.Datetime(string='Pickup Time From')
    schedule_pickup_time_to = fields.Datetime(string='Pickup Time To')
    deliver_order_date = fields.Datetime(string='Deliver Order Date')
    driver_name = fields.Char(string='Driver Name')
    driver_phone = fields.Char(string='Driver Phone')
    driver_license_plate = fields.Char(string='Driver License Plate')
    promo_code = fields.Char(string='Promo Code')
    delivery_status_id = fields.Many2one('delivery.status', string='Delivery Status', required=True)
    delivery_charge = fields.Monetary(string='Estimate Shipping Cost')
    real_delivery_charge = fields.Monetary(currency_field='currency_id', string='Real Shipping Cost')
    real_weight = fields.Float(string='Real Weight')
    weight_unit = fields.Selection(selection=[
        ('L', 'Pounds'),
        ('KG', 'Kilograms'),
        ('G', 'Grams')
    ], string='Weight Unit', required=True)
