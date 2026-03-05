import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class CodReconciliation(models.Model):
    _name = 'cod.reconciliation'
    _inherit = ['mail.thread']
    _description = 'COD Reconciliation'
    _order = 'create_date desc'
    name = fields.Char(string='Reference', required=True, default=lambda self: _('New'), readonly=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, index=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    carrier_id = fields.Many2one('delivery.carrier', string='Carrier', required=True, tracking=True, domain="[('is_support_auto_cod_reconciliation', '=', True)]")
    state = fields.Selection(selection=[('draft', 'Draft'), ('imported', 'Imported'), ('reconciling', 'Reconciling'), ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled')], string='Status', default='draft', required=True, tracking=True)
    import_file = fields.Binary(string='Import File', attachment=True)
    import_filename = fields.Char(string='Filename')
    import_date = fields.Datetime(string='Import Date', readonly=True)
    reconciliation_date = fields.Datetime(string='Reconciliation Date', readonly=True)
    period_date = fields.Date(string='Period Date', readonly=True)
    line_ids = fields.One2many('cod.reconciliation.line', 'reconciliation_id', string='Reconciliation Lines')
    carrier_total_cod = fields.Monetary(string='Carrier Total COD', currency_field='currency_id', readonly=True, help='Total COD amount per carrier report')
    carrier_total_shipping_fee = fields.Monetary(string='Carrier Total Shipping Fee', currency_field='currency_id', readonly=True, help='Total shipping fee per carrier report')
    carrier_net_amount = fields.Monetary(string='Carrier Net Amount', currency_field='currency_id', readonly=True, help='Net amount to be paid (COD - Fees) per carrier report')
    sys_total_cod = fields.Monetary(string='System Total COD', currency_field='currency_id', compute='_compute_summary', store=True)
    sys_total_shipping_fee = fields.Monetary(string='System Total Shipping Fee', currency_field='currency_id', compute='_compute_summary', store=True)
    total_cod_difference = fields.Monetary(string='Total COD Difference', currency_field='currency_id', compute='_compute_summary', store=True)
    total_fee_difference = fields.Monetary(string='Total Fee Difference', currency_field='currency_id', compute='_compute_summary', store=True)
    sys_net_amount = fields.Monetary(string='System Net Amount', currency_field='currency_id', compute='_compute_summary', store=True, help='Net amount computed from system (System COD - System Fees)')
    net_amount_difference = fields.Monetary(string='Net Amount Difference', currency_field='currency_id', compute='_compute_summary', store=True)
    notes = fields.Html(string='Notes')

    @api.model
    def create(self, vals_list):
        for OOOOOO0OOO00O0OOO in vals_list:
            if OOOOOO0OOO00O0OOO.get('name', _('New')) == _('New'):
                OOOOOO0OOO00O0OOO['name'] = self.env['ir.sequence'].next_by_code('cod.reconciliation') or _('New')
        return super().create(vals_list)

    def unlink(self):
        if any((rec.state == 'reconciled' for rec in self)):
            raise UserError(_('Cannot delete a reconciliation that has already been reconciled.'))
        return super().unlink()

    @api.depends('line_ids', 'line_ids.reconcile_status', 'line_ids.carrier_cod_amount', 'line_ids.sys_cod_amount', 'line_ids.carrier_shipping_fee', 'line_ids.sys_shipping_fee', 'line_ids.cod_difference', 'line_ids.fee_difference')
    def _compute_summary(self):
        for OO0O0OO000OOO0O0O in self:
            OOO0OO0OO00OOO0OO = OO0O0OO000OOO0O0O.line_ids
            OO0O0OO000OOO0O0O.sys_total_cod = sum(OOO0OO0OO00OOO0OO.mapped('sys_cod_amount'))
            OO0O0OO000OOO0O0O.sys_total_shipping_fee = sum(OOO0OO0OO00OOO0OO.mapped('sys_shipping_fee'))
            OO0O0OO000OOO0O0O.total_cod_difference = sum(OOO0OO0OO00OOO0OO.mapped('cod_difference'))
            OO0O0OO000OOO0O0O.total_fee_difference = sum(OOO0OO0OO00OOO0OO.mapped('fee_difference'))
            OO0O0OO000OOO0O0O.sys_net_amount = OO0O0OO000OOO0O0O.sys_total_cod - OO0O0OO000OOO0O0O.sys_total_shipping_fee
            OO0O0OO000OOO0O0O.net_amount_difference = OO0O0OO000OOO0O0O.carrier_net_amount - OO0O0OO000OOO0O0O.sys_net_amount

    def _parse_reconciliation_file(self, file_data, filename):
        raise UserError(_('No file parser is configured for this reconciliation. Please ensure the carrier module provides a parser.'))

    def action_reconcile(self):
        self.ensure_one()
        if self.state not in ('imported', 'reconciling'):
            raise UserError(_('Can only reconcile from Imported or Reconciling state.'))
        self.write({'state': 'reconciling'})
        OO000O00OO00O0000 = self.env['carrier.ref.order']
        for OO0O000000OOO0O00 in self.line_ids:
            if not OO0O000000OOO0O00.carrier_bill_code:
                OO0O000000OOO0O00.write({'reconcile_status': 'not_found', 'reconcile_note': _('No bill code')})
                continue
            OO00O00O0OOOO0O0O = OO000O00OO00O0000.search([('carrier_tracking_ref', '=', OO0O000000OOO0O00.carrier_bill_code), ('company_id', '=', self.company_id.id)], limit=1)
            if not OO00O00O0OOOO0O0O:
                OO0O000000OOO0O00.write({'reconcile_status': 'not_found', 'reconcile_note': _('Tracking ref %s not found in system', OO0O000000OOO0O00.carrier_bill_code)})
                continue
            OO0O000000OOO0O00.write({'carrier_ref_order_id': OO00O00O0OOOO0O0O.id, 'sys_cod_amount': OO00O00O0OOOO0O0O.cash_on_delivery_amount, 'sys_shipping_fee': OO00O00O0OOOO0O0O.real_delivery_charge or OO00O00O0OOOO0O0O.delivery_charge, 'sale_order_id': OO00O00O0OOOO0O0O.sale_id.id, 'picking_id': OO00O00O0OOOO0O0O.picking_id.id})
            O00OOO00OOOO0O0O0 = abs(OO0O000000OOO0O00.carrier_cod_amount - OO0O000000OOO0O00.sys_cod_amount)
            O00O0O00000OO0000 = abs(OO0O000000OOO0O00.carrier_shipping_fee - OO0O000000OOO0O00.sys_shipping_fee)
            if O00OOO00OOOO0O0O0 < 1.0 and O00O0O00000OO0000 < 1.0:
                O0OOOOOOOOO00000O = 'matched'
                O000OOOOOOOOOO000 = _('Fully matched')
            else:
                O0OOOOOOOOO00000O = 'mismatched'
                O00O00O000OOOOOOO = []
                if O00OOO00OOOO0O0O0 >= 1.0:
                    O00O00O000OOOOOOO.append(_('COD difference: %(diff)s (Carrier: %(carrier)s, System: %(sys)s)', diff=O00OOO00OOOO0O0O0, carrier=OO0O000000OOO0O00.carrier_cod_amount, sys=OO0O000000OOO0O00.sys_cod_amount))
                if O00O0O00000OO0000 >= 1.0:
                    O00O00O000OOOOOOO.append(_('Fee difference: %(diff)s (Carrier: %(carrier)s, System: %(sys)s)', diff=O00O0O00000OO0000, carrier=OO0O000000OOO0O00.carrier_shipping_fee, sys=OO0O000000OOO0O00.sys_shipping_fee))
                O000OOOOOOOOOO000 = '; '.join(O00O00O000OOOOOOO)
            OO0O000000OOO0O00.write({'reconcile_status': O0OOOOOOOOO00000O, 'reconcile_note': O000OOOOOOOOOO000})
            OOOO0O00O0O00000O = {'cod_reconcile_status': O0OOOOOOOOO00000O, 'cod_reconciliation_id': self.id}
            if OO00O00O0OOOO0O0O.real_delivery_charge != OO0O000000OOO0O00.carrier_shipping_fee and OO0O000000OOO0O00.carrier_shipping_fee > 0:
                OOOO0O00O0O00000O['real_delivery_charge'] = OO0O000000OOO0O00.carrier_shipping_fee
            OO00O00O0OOOO0O0O.write(OOOO0O00O0O00000O)
        self.write({'state': 'reconciled', 'reconciliation_date': fields.Datetime.now()})
        O00OOO0OO0OOO0OOO = self.line_ids.filtered(lambda l: l.reconcile_status == 'not_found' and l.carrier_bill_code).mapped('carrier_bill_code')
        OO00O0O0OO0OOO0OO = len(self.line_ids)
        O0000O000OOO00OO0 = len(self.line_ids.filtered(lambda l: l.reconcile_status == 'matched'))
        O0O0000O0OOOO00OO = len(self.line_ids.filtered(lambda l: l.reconcile_status == 'mismatched'))
        OOO000OOO00OOOO00 = len(self.line_ids.filtered(lambda l: l.reconcile_status == 'not_found'))
        O0O0OO0O00OO0O0OO = O0000O000OOO00OO0 / OO00O0O0OO0OOO0OO * 100 if OO00O0O0OO0OOO0OO else 0.0
        O0OO00O0000OO0O00 = _('Reconciliation completed: %(matched)s matched, %(mismatched)s mismatched, %(not_found)s not found out of %(total)s lines.', matched=O0000O000OOO00OO0, mismatched=O0O0000O0OOOO00OO, not_found=OOO000OOO00OOOO00, total=OO00O0O0OO0OOO0OO)
        if O00OOO0OO0OOO0OOO:
            O0OO00O0000OO0O00 += '<br/><br/>' + _('<b>Not found bill codes:</b><br/>%s', '<br/>'.join(O00OOO0OO0OOO0OOO))
        self.message_post(body=O0OO00O0000OO0O00, message_type='comment', subtype_xmlid='mail.mt_note')
        OO0000OOO0O00OOO0 = _('%(matched)s/%(total)s lines matched (%(rate).1f%%). %(mismatched)s mismatched, %(not_found)s not found.', matched=O0000O000OOO00OO0, total=OO00O0O0OO0OOO0OO, rate=O0O0OO0O00OO0O0OO, mismatched=O0O0000O0OOOO00OO, not_found=OOO000OOO00OOOO00)
        if O00OOO0OO0OOO0OOO:
            OO0000OOO0O00OOO0 += '\n' + _('Not found: %s', ', '.join(O00OOO0OO0OOO0OOO))
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': _('Reconciliation Complete'), 'message': OO0000OOO0O00OOO0, 'type': 'success' if O0O0OO0O00OO0O0OO == 100 else 'warning', 'sticky': True, 'next': {'type': 'ir.actions.act_window_close'}}}

    def action_reset_to_draft(self):
        self.ensure_one()
        OO000OOOOOOO0OOO0 = self.line_ids.mapped('carrier_ref_order_id')
        if OO000OOOOOOO0OOO0:
            OO000OOOOOOO0OOO0.write({'cod_reconcile_status': False, 'cod_reconciliation_id': False})
        self.line_ids.unlink()
        self.write({'state': 'draft', 'reconciliation_date': False, 'import_date': False, 'carrier_total_cod': 0, 'carrier_total_shipping_fee': 0, 'carrier_net_amount': 0, 'period_date': False})

    def action_cancel(self):
        self.ensure_one()
        OO00O00O0OO000O0O = self.line_ids.mapped('carrier_ref_order_id')
        if OO00O00O0OO000O0O:
            OO00O00O0OO000O0O.write({'cod_reconcile_status': False, 'cod_reconciliation_id': False})
        self.write({'state': 'cancelled'})

    def action_open_import_wizard(self):
        self.ensure_one()
        return {'name': _('Import COD Reconciliation File'), 'type': 'ir.actions.act_window', 'res_model': 'cod.reconciliation.import.wizard', 'view_mode': 'form', 'target': 'new', 'context': {'default_reconciliation_id': self.id}}

class CodReconciliationLine(models.Model):
    _name = 'cod.reconciliation.line'
    _description = 'COD Reconciliation Line'
    _order = 'sequence, id'
    reconciliation_id = fields.Many2one('cod.reconciliation', string='Reconciliation', required=True, ondelete='cascade', index=True)
    currency_id = fields.Many2one(related='reconciliation_id.currency_id')
    sequence = fields.Integer(string='STT', default=10)
    carrier_bill_code = fields.Char(string='Bill Code', index=True)
    carrier_send_date = fields.Date(string='Send Date')
    carrier_service = fields.Char(string='Service')
    carrier_delivery_date = fields.Date(string='Delivery Date')
    carrier_cod_amount = fields.Monetary(string='Carrier COD Amount', currency_field='currency_id')
    carrier_weight = fields.Float(string='Carrier Weight')
    carrier_shipping_fee = fields.Monetary(string='Carrier Shipping Fee', currency_field='currency_id')
    carrier_collected_fee = fields.Monetary(string='Carrier Collected Fee', currency_field='currency_id')
    carrier_discount = fields.Monetary(string='Carrier Discount', currency_field='currency_id')
    carrier_total_fee = fields.Monetary(string='Carrier Total Fee', currency_field='currency_id')
    carrier_note = fields.Char(string='Carrier Note')
    carrier_ref_order_id = fields.Many2one('carrier.ref.order', string='Carrier Ref Order', readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    picking_id = fields.Many2one('stock.picking', string='Picking', readonly=True)
    sys_cod_amount = fields.Monetary(string='System COD Amount', currency_field='currency_id', readonly=True)
    sys_shipping_fee = fields.Monetary(string='System Shipping Fee', currency_field='currency_id', readonly=True)
    reconcile_status = fields.Selection(selection=[('pending', 'Pending'), ('matched', 'Matched'), ('mismatched', 'Mismatched'), ('not_found', 'Not Found')], string='Status', default='pending', required=True, index=True)
    cod_difference = fields.Monetary(string='COD Difference', currency_field='currency_id', compute='_compute_differences', store=True)
    fee_difference = fields.Monetary(string='Fee Difference', currency_field='currency_id', compute='_compute_differences', store=True)
    reconcile_note = fields.Char(string='Reconcile Note')

    @api.depends('carrier_cod_amount', 'sys_cod_amount', 'carrier_shipping_fee', 'sys_shipping_fee')
    def _compute_differences(self):
        for O0O00O0O0OOOO0OO0 in self:
            O0O00O0O0OOOO0OO0.cod_difference = O0O00O0O0OOOO0OO0.carrier_cod_amount - O0O00O0O0OOOO0OO0.sys_cod_amount
            O0O00O0O0OOOO0OO0.fee_difference = O0O00O0O0OOOO0OO0.carrier_shipping_fee - O0O00O0O0OOOO0OO0.sys_shipping_fee