from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CarrierRefOrder(models.Model):
    _name = 'carrier.ref.order'
    _inherit = ['mail.thread']
    _rec_name = 'carrier_tracking_ref'
    _order = 'create_date desc'
    _description = 'Carrier Ref Order'
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    picking_id = fields.Many2one('stock.picking', string='Picking', required=True)
    sale_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    carrier_id = fields.Many2one('delivery.carrier', string='Carrier', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, index=True)
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
    mapped_status_id = fields.Many2one('delivery.standard.status', string='Mapped Status', compute='_compute_mapped_status_id', store=True)
    mapped_status = fields.Selection(selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'), ('picking_up', 'Picking Up'), ('picked_up', 'Picked Up'), ('in_transit', 'In Transit'), ('delivering', 'Delivering'), ('delivered', 'Delivered'), ('returning', 'Returning'), ('returned', 'Returned'), ('cancelled', 'Cancelled'), ('failed', 'Failed'), ('exception', 'Exception')], string='Standard Status', compute='_compute_mapped_status_id', store=True)
    delivery_charge = fields.Monetary(string='Estimate Shipping Cost')
    real_delivery_charge = fields.Monetary(currency_field='currency_id', string='Real Shipping Cost')
    real_weight = fields.Float(string='Real Weight')
    weight_unit = fields.Selection(selection=[('L', 'Pounds'), ('KG', 'Kilograms'), ('G', 'Grams')], string='Weight Unit', required=True)
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order', readonly=True, copy=False, tracking=True)
    purchase_count = fields.Integer(string='PO Count', compute='_compute_purchase_count')
    invoice_status = fields.Selection(related='purchase_id.invoice_status', string='Invoice Status')
    payment_status = fields.Selection([('not_paid', 'Not Paid'), ('in_payment', 'In Payment'), ('paid', 'Paid'), ('partial', 'Partially Paid'), ('reversed', 'Reversed'), ('invoicing_legacy', 'Invoicing App Legacy'), ('no_invoice', 'No Invoice')], string='Payment Status', compute='_compute_payment_status', store=True)
    cod_reconcile_status = fields.Selection(selection=[('pending', 'Pending'), ('matched', 'Matched'), ('mismatched', 'Mismatched')], string='COD Status', copy=False, index=True, tracking=True)
    cod_reconciliation_id = fields.Many2one('cod.reconciliation', string='COD Reconciliation', readonly=True, copy=False)

    def _compute_purchase_count(self):
        for OOOOOO0OOO00O0OOO in self:
            OOOOOO0OOO00O0OOO.purchase_count = 1 if OOOOOO0OOO00O0OOO.purchase_id else 0

    @api.depends('delivery_status_id', 'carrier_id.status_mapping_ids')
    def _compute_mapped_status_id(self):
        for OO0O0OO000OOO0O0O in self:
            OOO0OO0OO00OOO0OO = OO0O0OO000OOO0O0O.carrier_id.get_mapped_standard_status(OO0O0OO000OOO0O0O.delivery_status_id) if OO0O0OO000OOO0O0O.carrier_id else self.env['delivery.standard.status']
            OO0O0OO000OOO0O0O.mapped_status_id = OOO0OO0OO00OOO0OO.id if OOO0OO0OO00OOO0OO else False
            OO0O0OO000OOO0O0O.mapped_status = OOO0OO0OO00OOO0OO.code if OOO0OO0OO00OOO0OO else False

    @api.depends('purchase_id.invoice_ids.payment_state', 'purchase_id.invoice_ids.state')
    def _compute_payment_status(self):
        for OO000O00OO00O0000 in self:
            if not OO000O00OO00O0000.purchase_id or not OO000O00OO00O0000.purchase_id.invoice_ids:
                OO000O00OO00O0000.payment_status = 'no_invoice'
            else:
                OO0O000000OOO0O00 = OO000O00OO00O0000.purchase_id.invoice_ids.filtered(lambda inv: inv.state == 'posted' and inv.move_type in ('in_invoice', 'in_receipt'))
                if not OO0O000000OOO0O00:
                    OO000O00OO00O0000.payment_status = 'no_invoice'
                    continue
                OO00O00O0OOOO0O0O = OO0O000000OOO0O00.mapped('payment_state')
                if 'not_paid' in OO00O00O0OOOO0O0O:
                    OO000O00OO00O0000.payment_status = 'not_paid'
                elif 'partial' in OO00O00O0OOOO0O0O:
                    OO000O00OO00O0000.payment_status = 'partial'
                elif 'in_payment' in OO00O00O0OOOO0O0O:
                    OO000O00OO00O0000.payment_status = 'in_payment'
                elif all((state == 'paid' for state in OO00O00O0OOOO0O0O if state)):
                    OO000O00OO00O0000.payment_status = 'paid'
                elif 'reversed' in OO00O00O0OOOO0O0O:
                    OO000O00OO00O0000.payment_status = 'reversed'
                else:
                    OO000O00OO00O0000.payment_status = 'no_invoice'

    def _get_vendor_for_record(self, record):
        O00OOO00OOOO0O0O0 = record.carrier_id
        if O00OOO00OOOO0O0O0.external_carrier_id:
            return O00OOO00OOOO0O0O0.external_carrier_id
        O00O0O00000OO0000 = O00OOO00OOOO0O0O0.product_id
        if O00O0O00000OO0000 and O00O0O00000OO0000.seller_ids:
            return O00O0O00000OO0000.seller_ids[:1].partner_id
        raise UserError(_('No vendor found for carrier "%(carrier)s". Please configure either:\n- An "External Carrier" (external_carrier_id) on the carrier, or\n- A Vendor (Supplier) on the delivery product "%(product)s".', carrier=O00OOO00OOOO0O0O0.name, product=O00O0O00000OO0000.name if O00O0O00000OO0000 else _('N/A')))

    def action_create_purchase_order(self):
        O0OOOOOOOOO00000O = self.filtered(lambda r: not r.purchase_id or r.purchase_id.state in ('draft', 'sent'))
        O000OOOOOOOOOO000 = self - O0OOOOOOOOO00000O
        if not O0OOOOOOOOO00000O:
            raise UserError(_('All selected records are already linked to confirmed Purchase Orders.'))
        O00O00O000OOOOOOO = {}
        for OOOO0O00O0O00000O in O0OOOOOOOOO00000O:
            O00OOO0OO0OOO0OOO = OOOO0O00O0O00000O.carrier_id.product_id
            if not O00OOO0OO0OOO0OOO:
                raise UserError(_('Please configure a Delivery Product on the carrier "%s" to create a Purchase Order.', OOOO0O00O0O00000O.carrier_id.name))
            OO00O0O0OO0OOO0OO = self._get_vendor_for_record(OOOO0O00O0O00000O)
            O00O00O000OOOOOOO.setdefault(OO00O0O0OO0OOO0OO, self.env['carrier.ref.order'])
            O00O00O000OOOOOOO[OO00O0O0OO0OOO0OO] |= OOOO0O00O0O00000O
        O0000O000OOO00OO0 = []
        for OO00O0O0OO0OOO0OO, O0O0000O0OOOO00OO in O00O00O000OOOOOOO.items():
            OOO000OOO00OOOO00 = O0O0000O0OOOO00OO.mapped('purchase_id').filtered(lambda po: po.state in ('draft', 'sent'))
            if OOO000OOO00OOOO00:
                O0O0OO0O00OO0O0OO = OOO000OOO00OOOO00[0]
                for O0OO00O0000OO0O00 in OOO000OOO00OOOO00[1:]:
                    O0OO00O0000OO0O00.order_line.write({'order_id': O0O0OO0O00OO0O0OO.id})
                    if O0OO00O0000OO0O00.origin and O0OO00O0000OO0O00.origin not in (O0O0OO0O00OO0O0OO.origin or ''):
                        O0O0OO0O00OO0O0OO.origin = f"{O0O0OO0O00OO0O0OO.origin or ''}, {O0OO00O0000OO0O00.origin}".strip(', ')
                    O0OO00O0000OO0O00.button_cancel()
                    O0OO00O0000OO0O00.unlink()
            else:
                OO0000OOO0O00OOO0 = [r.carrier_tracking_ref for r in O0O0000O0OOOO00OO if r.carrier_tracking_ref]
                if not OO0000OOO0O00OOO0:
                    OO0000OOO0O00OOO0 = [r.picking_id.name for r in O0O0000O0OOOO00OO if r.picking_id]
                OO000OOOOOOO0OOO0 = ', '.join(OO0000OOO0O00OOO0[:5]) + ('...' if len(OO0000OOO0O00OOO0) > 5 else '')
                O0O0OO0O00OO0O0OO = self.env['purchase.order'].create({'partner_id': OO00O0O0OO0OOO0OO.id, 'origin': OO000OOOOOOO0OOO0})
            O0000O000OOO00OO0.append(O0O0OO0O00OO0O0OO.id)
            for OOOO0O00O0O00000O in O0O0000O0OOOO00OO:
                if OOOO0O00O0O00000O.purchase_id == O0O0OO0O00OO0O0OO:
                    continue
                O00OOO0OO0OOO0OOO = OOOO0O00O0O00000O.carrier_id.product_id
                self.env['purchase.order.line'].create({'order_id': O0O0OO0O00OO0O0OO.id, 'product_id': O00OOO0OO0OOO0OOO.id, 'name': f'DO: {OOOO0O00O0O00000O.picking_id.name} - Ref: {OOOO0O00O0O00000O.carrier_tracking_ref}', 'product_qty': 1, 'price_unit': OOOO0O00O0O00000O.real_delivery_charge or OOOO0O00O0O00000O.delivery_charge, 'product_uom_id': O00OOO0OO0OOO0OOO.uom_id.id})
                OOOO0O00O0O00000O.purchase_id = O0O0OO0O00OO0O0OO.id
        if O000OOOOOOOOOO000:
            OO00O00O0OO000O0O = ', '.join(O000OOOOOOOOOO000.mapped('carrier_tracking_ref'))
            O0OOOOOOOOO00000O[0].message_post(body=_('Skipped records already linked to confirmed PO: %s', OO00O00O0OO000O0O), message_type='comment', subtype_xmlid='mail.mt_note')
        O0O00O0O0OOOO0OO0 = self.env['purchase.order'].browse(O0000O000OOO00OO0).mapped('name')
        for OOOO0O00O0O00000O in O0OOOOOOOOO00000O:
            OOOO0O00O0O00000O.message_post(body=_('Purchase Order created/merged: %s', ', '.join(O0O00O0O0OOOO0OO0)), message_type='comment', subtype_xmlid='mail.mt_note')
        if len(O0000O000OOO00OO0) == 1:
            return {'type': 'ir.actions.act_window', 'name': _('Purchase Order'), 'res_model': 'purchase.order', 'res_id': O0000O000OOO00OO0[0], 'view_mode': 'form'}
        elif len(O0000O000OOO00OO0) > 1:
            return {'type': 'ir.actions.act_window', 'name': _('Purchase Orders'), 'res_model': 'purchase.order', 'domain': [('id', 'in', O0000O000OOO00OO0)], 'view_mode': 'list,form'}
        return True

    def action_unlink_purchase_order(self):
        for O0000O00OOO00O0O0 in self:
            if not O0000O00OOO00O0O0.purchase_id:
                continue
            if O0000O00OOO00O0O0.purchase_id.state not in ('draft', 'sent'):
                raise UserError(_('Cannot unlink Purchase Order "%(po)s" because it is already confirmed. Only draft Purchase Orders can be unlinked.', po=O0000O00OOO00O0O0.purchase_id.name))
            OOO0OOOO0O000O000 = O0000O00OOO00O0O0.purchase_id
            OO00OOO00OO00OO0O = OOO0OOOO0O000O000.name
            OOO0O00OOO0O0O0OO = OOO0OOOO0O000O000.order_line.filtered(lambda l: l.name == O0000O00OOO00O0O0.carrier_tracking_ref)
            if OOO0O00OOO0O0O0OO:
                OOO0O00OOO0O0O0OO.unlink()
            O0000O00OOO00O0O0.purchase_id = False
            O0000O00OOO00O0O0.message_post(body=_('Unlinked from Purchase Order: %s', OO00OOO00OO00OO0O), message_type='comment', subtype_xmlid='mail.mt_note')
            if not OOO0OOOO0O000O000.order_line:
                OOO0OOOO0O000O000.button_cancel()
                OOO0OOOO0O000O000.unlink()

    def action_view_purchase_order(self):
        self.ensure_one()
        if not self.purchase_id:
            raise UserError(_('No Purchase Order is linked to this record.'))
        return {'type': 'ir.actions.act_window', 'name': _('Purchase Order'), 'res_model': 'purchase.order', 'res_id': self.purchase_id.id, 'view_mode': 'form'}