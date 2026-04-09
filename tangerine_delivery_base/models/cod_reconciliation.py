# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CodReconciliation(models.Model):
    _name = 'cod.reconciliation'
    _inherit = ['mail.thread']
    _description = 'COD Reconciliation'
    _order = 'create_date desc'

    name = fields.Char(
        string='Reference',
        required=True,
        default=lambda self: _('New'),
        readonly=True,
        copy=False,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )
    carrier_id = fields.Many2one(
        'delivery.carrier',
        string='Carrier',
        required=True,
        tracking=True,
        domain="[('is_support_auto_cod_reconciliation', '=', True)]",
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('imported', 'Imported'),
            ('reconciling', 'Reconciling'),
            ('reconciled', 'Reconciled'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )

    # File info
    import_file = fields.Binary(string='Import File', attachment=True)
    import_filename = fields.Char(string='Filename')
    import_date = fields.Datetime(string='Import Date', readonly=True)
    reconciliation_date = fields.Datetime(string='Reconciliation Date', readonly=True)
    period_date = fields.Date(string='Period Date', readonly=True)

    # Lines
    line_ids = fields.One2many(
        'cod.reconciliation.line',
        'reconciliation_id',
        string='Reconciliation Lines',
    )

    # Summary - from carrier report
    carrier_total_cod = fields.Monetary(
        string='Carrier Total COD',
        currency_field='currency_id',
        readonly=True,
        help='Total COD amount per carrier report',
    )
    carrier_total_shipping_fee = fields.Monetary(
        string='Carrier Total Shipping Fee',
        currency_field='currency_id',
        readonly=True,
        help='Total shipping fee per carrier report',
    )
    carrier_net_amount = fields.Monetary(
        string='Carrier Net Amount',
        currency_field='currency_id',
        readonly=True,
        help='Net amount to be paid (COD - Fees) per carrier report',
    )


    # Summary - computed from system
    sys_total_cod = fields.Monetary(
        string='System Total COD',
        currency_field='currency_id',
        compute='_compute_summary',
        store=True,
    )
    sys_total_shipping_fee = fields.Monetary(
        string='System Total Shipping Fee',
        currency_field='currency_id',
        compute='_compute_summary',
        store=True,
    )


    total_cod_difference = fields.Monetary(
        string='Total COD Difference',
        currency_field='currency_id',
        compute='_compute_summary',
        store=True,
    )
    total_fee_difference = fields.Monetary(
        string='Total Fee Difference',
        currency_field='currency_id',
        compute='_compute_summary',
        store=True,
    )
    sys_net_amount = fields.Monetary(
        string='System Net Amount',
        currency_field='currency_id',
        compute='_compute_summary',
        store=True,
        help='Net amount computed from system (System COD - System Fees)',
    )
    net_amount_difference = fields.Monetary(
        string='Net Amount Difference',
        currency_field='currency_id',
        compute='_compute_summary',
        store=True,
    )

    notes = fields.Html(string='Notes')

    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('cod.reconciliation') or _('New')
        return super().create(vals_list)

    def unlink(self):
        if any(rec.state == 'reconciled' for rec in self):
            raise UserError(_('Cannot delete a reconciliation that has already been reconciled.'))
        return super().unlink()

    @api.depends(
        'line_ids',
        'line_ids.reconcile_status',
        'line_ids.carrier_cod_amount',
        'line_ids.sys_cod_amount',
        'line_ids.carrier_shipping_fee',
        'line_ids.sys_shipping_fee',
        'line_ids.cod_difference',
        'line_ids.fee_difference',
    )
    def _compute_summary(self):
        for rec in self:
            lines = rec.line_ids
            rec.sys_total_cod = sum(lines.mapped('sys_cod_amount'))
            rec.sys_total_shipping_fee = sum(lines.mapped('sys_shipping_fee'))
            rec.total_cod_difference = sum(lines.mapped('cod_difference'))
            rec.total_fee_difference = sum(lines.mapped('fee_difference'))
            rec.sys_net_amount = rec.sys_total_cod - rec.sys_total_shipping_fee
            rec.net_amount_difference = rec.carrier_net_amount - rec.sys_net_amount

    def _parse_reconciliation_file(self, file_data, filename):
        """Parse the reconciliation file and return lines data + metadata.

        To be overridden by carrier-specific modules.

        :param file_data: raw bytes of the uploaded file
        :param filename: original filename
        :returns: dict with keys:
            - 'lines': list of dicts for cod.reconciliation.line creation
            - 'carrier_total_cod': float
            - 'carrier_total_shipping_fee': float
            - 'carrier_net_amount': float
            - 'period_date': date or False
            - any extra carrier-specific fields
        """
        raise UserError(_(
            'No file parser is configured for this reconciliation. '
            'Please ensure the carrier module provides a parser.'
        ))

    def action_reconcile(self):
        """Perform automatic reconciliation against system data."""
        self.ensure_one()
        if self.state not in ('imported', 'reconciling'):
            raise UserError(_('Can only reconcile from Imported or Reconciling state.'))

        self.write({'state': 'reconciling'})

        CarrierRef = self.env['carrier.ref.order']
        for line in self.line_ids:
            if not line.carrier_bill_code:
                line.write({'reconcile_status': 'not_found', 'reconcile_note': _('No bill code')})
                continue

            # Search by tracking ref
            ref_order = CarrierRef.search([
                ('carrier_tracking_ref', '=', line.carrier_bill_code),
                ('company_id', '=', self.company_id.id),
            ], limit=1)

            if not ref_order:
                line.write({
                    'reconcile_status': 'not_found',
                    'reconcile_note': _('Tracking ref %s not found in system', line.carrier_bill_code),
                })
                continue

            line.write({
                'carrier_ref_order_id': ref_order.id,
                'sys_cod_amount': ref_order.cash_on_delivery_amount,
                'sys_shipping_fee': ref_order.real_delivery_charge or ref_order.delivery_charge,
                'sale_order_id': ref_order.sale_id.id,
                'picking_id': ref_order.picking_id.id,
            })

            # Compare amounts
            cod_diff = abs(line.carrier_cod_amount - line.sys_cod_amount)
            fee_diff = abs(line.carrier_shipping_fee - line.sys_shipping_fee)

            if cod_diff < 1.0 and fee_diff < 1.0:
                status = 'matched'
                note = _('Fully matched')
            else:
                status = 'mismatched'
                notes = []
                if cod_diff >= 1.0:
                    notes.append(
                        _('COD difference: %(diff)s (Carrier: %(carrier)s, System: %(sys)s)',
                          diff=cod_diff, carrier=line.carrier_cod_amount, sys=line.sys_cod_amount)
                    )
                if fee_diff >= 1.0:
                    notes.append(
                        _('Fee difference: %(diff)s (Carrier: %(carrier)s, System: %(sys)s)',
                          diff=fee_diff, carrier=line.carrier_shipping_fee, sys=line.sys_shipping_fee)
                    )
                note = '; '.join(notes)

            line.write({
                'reconcile_status': status,
                'reconcile_note': note,
            })

            # Update carrier.ref.order with COD status and real cost
            ref_update = {
                'cod_reconcile_status': status,
                'cod_reconciliation_id': self.id,
            }
            if ref_order.real_delivery_charge != line.carrier_shipping_fee and line.carrier_shipping_fee > 0:
                ref_update['real_delivery_charge'] = line.carrier_shipping_fee
            ref_order.write(ref_update)

        self.write({
            'state': 'reconciled',
            'reconciliation_date': fields.Datetime.now(),
        })

        # Collect not-found bill codes
        not_found_codes = self.line_ids.filtered(
            lambda l: l.reconcile_status == 'not_found' and l.carrier_bill_code
        ).mapped('carrier_bill_code')

        total_lines = len(self.line_ids)
        matched_lines = len(self.line_ids.filtered(lambda l: l.reconcile_status == 'matched'))
        mismatched_lines = len(self.line_ids.filtered(lambda l: l.reconcile_status == 'mismatched'))
        not_found_lines = len(self.line_ids.filtered(lambda l: l.reconcile_status == 'not_found'))
        match_rate = (matched_lines / total_lines * 100) if total_lines else 0.0

        chatter_body = _(
            'Reconciliation completed: %(matched)s matched, %(mismatched)s mismatched, '
            '%(not_found)s not found out of %(total)s lines.',
            matched=matched_lines,
            mismatched=mismatched_lines,
            not_found=not_found_lines,
            total=total_lines,
        )
        if not_found_codes:
            chatter_body += '<br/><br/>' + _('<b>Not found bill codes:</b><br/>%s', '<br/>'.join(not_found_codes))

        self.message_post(
            body=chatter_body,
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )

        notification_msg = _(
            '%(matched)s/%(total)s lines matched (%(rate).1f%%). '
            '%(mismatched)s mismatched, %(not_found)s not found.',
            matched=matched_lines,
            total=total_lines,
            rate=match_rate,
            mismatched=mismatched_lines,
            not_found=not_found_lines,
        )
        if not_found_codes:
            notification_msg += '\n' + _('Not found: %s', ', '.join(not_found_codes))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reconciliation Complete'),
                'message': notification_msg,
                'type': 'success' if match_rate == 100 else 'warning',
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def action_reset_to_draft(self):
        """Reset reconciliation to draft state and clear all lines."""
        self.ensure_one()
        # Clear COD status on linked carrier ref orders
        linked_refs = self.line_ids.mapped('carrier_ref_order_id')
        if linked_refs:
            linked_refs.write({
                'cod_reconcile_status': False,
                'cod_reconciliation_id': False,
            })
        self.line_ids.unlink()
        self.write({
            'state': 'draft',
            'reconciliation_date': False,
            'import_date': False,
            'carrier_total_cod': 0,
            'carrier_total_shipping_fee': 0,
            'carrier_net_amount': 0,
            'period_date': False,
        })

    def action_cancel(self):
        """Cancel the reconciliation."""
        self.ensure_one()
        linked_refs = self.line_ids.mapped('carrier_ref_order_id')
        if linked_refs:
            linked_refs.write({
                'cod_reconcile_status': False,
                'cod_reconciliation_id': False,
            })
        self.write({'state': 'cancelled'})

    def action_open_import_wizard(self):
        """Open the import wizard for this reconciliation."""
        self.ensure_one()
        return {
            'name': _('Import COD Reconciliation File'),
            'type': 'ir.actions.act_window',
            'res_model': 'cod.reconciliation.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_reconciliation_id': self.id,
            },
        }


class CodReconciliationLine(models.Model):
    _name = 'cod.reconciliation.line'
    _description = 'COD Reconciliation Line'
    _order = 'sequence, id'

    reconciliation_id = fields.Many2one(
        'cod.reconciliation',
        string='Reconciliation',
        required=True,
        ondelete='cascade',
        index=True,
    )
    currency_id = fields.Many2one(related='reconciliation_id.currency_id')
    sequence = fields.Integer(string='STT', default=10)

    # Carrier-reported data (from file import)
    carrier_bill_code = fields.Char(string='Bill Code', index=True)
    carrier_send_date = fields.Date(string='Send Date')
    carrier_service = fields.Char(string='Service')
    carrier_delivery_date = fields.Date(string='Delivery Date')
    carrier_cod_amount = fields.Monetary(
        string='Carrier COD Amount',
        currency_field='currency_id',
    )
    carrier_weight = fields.Float(string='Carrier Weight')
    carrier_shipping_fee = fields.Monetary(
        string='Carrier Shipping Fee',
        currency_field='currency_id',
    )
    carrier_collected_fee = fields.Monetary(
        string='Carrier Collected Fee',
        currency_field='currency_id',
    )
    carrier_discount = fields.Monetary(
        string='Carrier Discount',
        currency_field='currency_id',
    )
    carrier_total_fee = fields.Monetary(
        string='Carrier Total Fee',
        currency_field='currency_id',
    )
    carrier_note = fields.Char(string='Carrier Note')

    # System data (computed during reconciliation)
    carrier_ref_order_id = fields.Many2one(
        'carrier.ref.order',
        string='Carrier Ref Order',
        readonly=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        readonly=True,
    )
    picking_id = fields.Many2one(
        'stock.picking',
        string='Picking',
        readonly=True,
    )
    sys_cod_amount = fields.Monetary(
        string='System COD Amount',
        currency_field='currency_id',
        readonly=True,
    )
    sys_shipping_fee = fields.Monetary(
        string='System Shipping Fee',
        currency_field='currency_id',
        readonly=True,
    )

    # Reconciliation result
    reconcile_status = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('matched', 'Matched'),
            ('mismatched', 'Mismatched'),
            ('not_found', 'Not Found'),
        ],
        string='Status',
        default='pending',
        required=True,
        index=True,
    )
    cod_difference = fields.Monetary(
        string='COD Difference',
        currency_field='currency_id',
        compute='_compute_differences',
        store=True,
    )
    fee_difference = fields.Monetary(
        string='Fee Difference',
        currency_field='currency_id',
        compute='_compute_differences',
        store=True,
    )
    reconcile_note = fields.Char(string='Reconcile Note')

    @api.depends('carrier_cod_amount', 'sys_cod_amount', 'carrier_shipping_fee', 'sys_shipping_fee')
    def _compute_differences(self):
        for line in self:
            line.cod_difference = line.carrier_cod_amount - line.sys_cod_amount
            line.fee_difference = line.carrier_shipping_fee - line.sys_shipping_fee
