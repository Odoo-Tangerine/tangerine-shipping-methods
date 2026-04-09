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
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        index=True,
    )
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
    mapped_status_id = fields.Many2one(
        'delivery.standard.status',
        string='Mapped Status',
        compute='_compute_mapped_status_id',
        store=True,
    )
    mapped_status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('picking_up', 'Picking Up'),
            ('picked_up', 'Picked Up'),
            ('in_transit', 'In Transit'),
            ('delivering', 'Delivering'),
            ('delivered', 'Delivered'),
            ('returning', 'Returning'),
            ('returned', 'Returned'),
            ('cancelled', 'Cancelled'),
            ('failed', 'Failed'),
            ('exception', 'Exception'),
        ],
        string='Standard Status',
        compute='_compute_mapped_status_id',
        store=True,
    )
    delivery_charge = fields.Monetary(string='Estimate Shipping Cost')
    real_delivery_charge = fields.Monetary(currency_field='currency_id', string='Real Shipping Cost')
    real_weight = fields.Float(string='Real Weight')
    weight_unit = fields.Selection(selection=[
        ('L', 'Pounds'),
        ('KG', 'Kilograms'),
        ('G', 'Grams')
    ], string='Weight Unit', required=True)

    purchase_id = fields.Many2one('purchase.order', string='Purchase Order', readonly=True, copy=False, tracking=True)
    purchase_count = fields.Integer(string='PO Count', compute='_compute_purchase_count')
    invoice_status = fields.Selection(related='purchase_id.invoice_status', string='Invoice Status')
    payment_status = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
        ('no_invoice', 'No Invoice')
    ], string='Payment Status', compute='_compute_payment_status', store=True)

    cod_reconcile_status = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('matched', 'Matched'),
            ('mismatched', 'Mismatched'),
        ],
        string='COD Status',
        copy=False,
        index=True,
        tracking=True,
    )
    cod_reconciliation_id = fields.Many2one(
        'cod.reconciliation',
        string='COD Reconciliation',
        readonly=True,
        copy=False,
    )

    def _compute_purchase_count(self):
        for record in self:
            record.purchase_count = 1 if record.purchase_id else 0


    @api.depends('delivery_status_id', 'carrier_id.status_mapping_ids')
    def _compute_mapped_status_id(self):
        for record in self:
            mapped = record.carrier_id.get_mapped_standard_status(
                record.delivery_status_id
            ) if record.carrier_id else self.env['delivery.standard.status']
            record.mapped_status_id = mapped.id if mapped else False
            record.mapped_status = mapped.code if mapped else False

    @api.depends('purchase_id.invoice_ids.payment_state', 'purchase_id.invoice_ids.state')
    def _compute_payment_status(self):
        for record in self:
            if not record.purchase_id or not record.purchase_id.invoice_ids:
                record.payment_status = 'no_invoice'
            else:
                invoices = record.purchase_id.invoice_ids.filtered(
                    lambda inv: inv.state == 'posted' and inv.move_type in ('in_invoice', 'in_receipt')
                )
                if not invoices:
                    record.payment_status = 'no_invoice'
                    continue
                states = invoices.mapped('payment_state')
                if 'not_paid' in states:
                    record.payment_status = 'not_paid'
                elif 'partial' in states:
                    record.payment_status = 'partial'
                elif 'in_payment' in states:
                    record.payment_status = 'in_payment'
                elif all(state == 'paid' for state in states if state):
                    record.payment_status = 'paid'
                elif 'reversed' in states:
                    record.payment_status = 'reversed'
                else:
                    record.payment_status = 'no_invoice'

    def _get_vendor_for_record(self, record):
        """Resolve vendor for a carrier ref order record.

        Priority:
        1. external_carrier_id on the carrier (explicit vendor config)
        2. First supplier from product's seller_ids
        3. Raise UserError
        """
        carrier = record.carrier_id
        if carrier.external_carrier_id:
            return carrier.external_carrier_id

        product = carrier.product_id
        if product and product.seller_ids:
            return product.seller_ids[:1].partner_id

        raise UserError(_(
            'No vendor found for carrier "%(carrier)s". '
            'Please configure either:\n'
            '- An "External Carrier" (external_carrier_id) on the carrier, or\n'
            '- A Vendor (Supplier) on the delivery product "%(product)s".',
            carrier=carrier.name,
            product=product.name if product else _('N/A'),
        ))

    def action_create_purchase_order(self):
        """Create or merge Purchase Orders for selected carrier ref orders.

        Logic:
        - Group records by vendor (resolved via _get_vendor_for_record)
        - Skip records already linked to a confirmed/locked PO
        - For records with existing draft POs: merge into the first draft PO
        - For records without PO: create a new PO or merge into existing draft
        """
        records_to_process = self.filtered(lambda r: not r.purchase_id or r.purchase_id.state in ('draft', 'sent'))
        skipped = self - records_to_process

        if not records_to_process:
            raise UserError(_('All selected records are already linked to confirmed Purchase Orders.'))

        records_by_vendor = {}
        for record in records_to_process:
            product = record.carrier_id.product_id
            if not product:
                raise UserError(_(
                    'Please configure a Delivery Product on the carrier "%s" to create a Purchase Order.',
                    record.carrier_id.name,
                ))

            vendor = self._get_vendor_for_record(record)
            records_by_vendor.setdefault(vendor, self.env['carrier.ref.order'])
            records_by_vendor[vendor] |= record

        action_res_ids = []

        for vendor, records in records_by_vendor.items():
            existing_draft_pos = records.mapped('purchase_id').filtered(
                lambda po: po.state in ('draft', 'sent')
            )

            if existing_draft_pos:
                target_po = existing_draft_pos[0]
                # Merge PO lines from other draft POs into the first one
                for other_po in existing_draft_pos[1:]:
                    other_po.order_line.write({'order_id': target_po.id})
                    # Update origin
                    if other_po.origin and other_po.origin not in (target_po.origin or ''):
                        target_po.origin = f"{target_po.origin or ''}, {other_po.origin}".strip(', ')
                    other_po.button_cancel()
                    other_po.unlink()
            else:
                origins = [r.carrier_tracking_ref for r in records if r.carrier_tracking_ref]
                if not origins:
                    origins = [r.picking_id.name for r in records if r.picking_id]
                origin_str = ', '.join(origins[:5]) + ('...' if len(origins) > 5 else '')
                target_po = self.env['purchase.order'].create({
                    'partner_id': vendor.id,
                    'origin': origin_str,
                })

            action_res_ids.append(target_po.id)

            for record in records:
                if record.purchase_id == target_po:
                    continue

                product = record.carrier_id.product_id
                self.env['purchase.order.line'].create({
                    'order_id': target_po.id,
                    'product_id': product.id,
                    'name': f"DO: {record.picking_id.name} - Ref: {record.carrier_tracking_ref}",
                    'product_qty': 1,
                    'price_unit': record.real_delivery_charge or record.delivery_charge,
                    'product_uom_id': product.uom_id.id,
                })
                record.purchase_id = target_po.id

        # Log messages
        if skipped:
            skipped_refs = ', '.join(skipped.mapped('carrier_tracking_ref'))
            records_to_process[0].message_post(
                body=_('Skipped records already linked to confirmed PO: %s', skipped_refs),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

        po_names = self.env['purchase.order'].browse(action_res_ids).mapped('name')
        for record in records_to_process:
            record.message_post(
                body=_('Purchase Order created/merged: %s', ', '.join(po_names)),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

        if len(action_res_ids) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Purchase Order'),
                'res_model': 'purchase.order',
                'res_id': action_res_ids[0],
                'view_mode': 'form',
            }
        elif len(action_res_ids) > 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Purchase Orders'),
                'res_model': 'purchase.order',
                'domain': [('id', 'in', action_res_ids)],
                'view_mode': 'list,form',
            }
        return True

    def action_unlink_purchase_order(self):
        """Unlink the Purchase Order from selected carrier ref orders.

        Only works for draft/sent POs. If the PO has no other lines
        remaining after removing these, the PO is cancelled and deleted.
        """
        for record in self:
            if not record.purchase_id:
                continue
            if record.purchase_id.state not in ('draft', 'sent'):
                raise UserError(_(
                    'Cannot unlink Purchase Order "%(po)s" because it is already confirmed. '
                    'Only draft Purchase Orders can be unlinked.',
                    po=record.purchase_id.name,
                ))

            po = record.purchase_id
            po_name = po.name

            # Remove the PO line that matches this record's tracking ref
            matching_lines = po.order_line.filtered(
                lambda l: l.name == record.carrier_tracking_ref
            )
            if matching_lines:
                matching_lines.unlink()

            record.purchase_id = False
            record.message_post(
                body=_('Unlinked from Purchase Order: %s', po_name),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

            # If PO has no lines left, cancel and delete it
            if not po.order_line:
                po.button_cancel()
                po.unlink()

    def action_view_purchase_order(self):
        """Open the linked Purchase Order in form view."""
        self.ensure_one()
        if not self.purchase_id:
            raise UserError(_('No Purchase Order is linked to this record.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Order'),
            'res_model': 'purchase.order',
            'res_id': self.purchase_id.id,
            'view_mode': 'form',
        }
