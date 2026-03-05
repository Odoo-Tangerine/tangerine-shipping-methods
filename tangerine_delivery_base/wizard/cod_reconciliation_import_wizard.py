import base64
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class CodReconciliationImportWizard(models.TransientModel):
    _name = 'cod.reconciliation.import.wizard'
    _description = 'COD Reconciliation Import Wizard'
    reconciliation_id = fields.Many2one('cod.reconciliation', string='Reconciliation')
    carrier_id = fields.Many2one('delivery.carrier', string='Carrier', required=True, domain="[('is_support_auto_cod_reconciliation', '=', True)]")
    delivery_type = fields.Selection(related='carrier_id.delivery_type')
    import_file = fields.Binary(string='Import File', required=True)
    import_filename = fields.Char(string='Filename')
    auto_reconcile = fields.Boolean(string='Auto Reconcile After Import', default=True, help='Automatically start reconciliation after importing the file.')

    @api.model
    def default_get(self, fields_list):
        OOOOOO0OOO00O0OOO = super().default_get(fields_list)
        if 'carrier_id' in fields_list and (not OOOOOO0OOO00O0OOO.get('carrier_id')):
            OO0O0OO000OOO0O0O = OOOOOO0OOO00O0OOO.get('reconciliation_id') or self.env.context.get('default_reconciliation_id')
            if OO0O0OO000OOO0O0O:
                OOO0OO0OO00OOO0OO = self.env['cod.reconciliation'].browse(OO0O0OO000OOO0O0O)
                if OOO0OO0OO00OOO0OO.carrier_id:
                    OOOOOO0OOO00O0OOO['carrier_id'] = OOO0OO0OO00OOO0OO.carrier_id.id
        return OOOOOO0OOO00O0OOO

    def action_import(self):
        self.ensure_one()
        if not self.import_file:
            raise UserError(_('Please select a file to import.'))
        OO000O00OO00O0000 = self.reconciliation_id
        if not OO000O00OO00O0000:
            OO000O00OO00O0000 = self.env['cod.reconciliation'].create({'carrier_id': self.carrier_id.id})
        if OO000O00OO00O0000.state not in ('draft', 'imported'):
            raise UserError(_('Can only import into Draft or Imported state.'))
        OO000O00OO00O0000.line_ids.unlink()
        OO0O000000OOO0O00 = base64.b64decode(self.import_file)
        OO00O00O0OOOO0O0O = OO000O00OO00O0000._parse_reconciliation_file(OO0O000000OOO0O00, self.import_filename)
        if not OO00O00O0OOOO0O0O or not OO00O00O0OOOO0O0O.get('lines'):
            raise UserError(_('No data lines found in the imported file.'))
        O00OOO00OOOO0O0O0 = self.env['carrier.ref.order']
        O00O0O00000OO0000 = [OOOO0O00O0O00000O.get('carrier_bill_code') for OOOO0O00O0O00000O in OO00O00O0OOOO0O0O['lines'] if OOOO0O00O0O00000O.get('carrier_bill_code')]
        if O00O0O00000OO0000:
            O0OOOOOOOOO00000O = O00OOO00OOOO0O0O0.search([('carrier_tracking_ref', 'in', O00O0O00000OO0000), ('company_id', '=', OO000O00OO00O0000.company_id.id)]).mapped('carrier_tracking_ref')
            O000OOOOOOOOOO000 = [code for code in O00O0O00000OO0000 if code not in O0OOOOOOOOO00000O]
            if O000OOOOOOOOOO000:
                raise UserError(_('The following %(count)s bill code(s) were not found in the system. Import has been cancelled.\n\n%(codes)s', count=len(O000OOOOOOOOOO000), codes=', '.join(O000OOOOOOOOOO000)))
        O00O00O000OOOOOOO = []
        for OOOO0O00O0O00000O in OO00O00O0OOOO0O0O['lines']:
            OOOO0O00O0O00000O['reconciliation_id'] = OO000O00OO00O0000.id
            O00O00O000OOOOOOO.append(OOOO0O00O0O00000O)
        self.env['cod.reconciliation.line'].create(O00O00O000OOOOOOO)
        O00OOO0OO0OOO0OOO = {'state': 'imported', 'import_date': fields.Datetime.now(), 'import_file': self.import_file, 'import_filename': self.import_filename, 'carrier_id': self.carrier_id.id, 'carrier_total_cod': OO00O00O0OOOO0O0O.get('carrier_total_cod', 0), 'carrier_total_shipping_fee': OO00O00O0OOOO0O0O.get('carrier_total_shipping_fee', 0), 'carrier_net_amount': OO00O00O0OOOO0O0O.get('carrier_net_amount', 0), 'period_date': OO00O00O0OOOO0O0O.get('period_date', False)}
        for OO00O0O0OO0OOO0OO, O0000O000OOO00OO0 in OO00O00O0OOOO0O0O.get('extra_vals', {}).items():
            O00OOO0OO0OOO0OOO[OO00O0O0OO0OOO0OO] = O0000O000OOO00OO0
        OO000O00OO00O0000.write(O00OOO0OO0OOO0OOO)
        OO000O00OO00O0000.message_post(body=_('Imported %(count)s lines from file "%(filename)s". Carrier Total COD: %(cod)s, Carrier Total Fees: %(fees)s.', count=len(O00O00O000OOOOOOO), filename=self.import_filename or 'N/A', cod=OO00O00O0OOOO0O0O.get('carrier_total_cod', 0), fees=OO00O00O0OOOO0O0O.get('carrier_total_shipping_fee', 0)), message_type='comment', subtype_xmlid='mail.mt_note')
        if self.auto_reconcile:
            OO000O00OO00O0000.action_reconcile()
        return {'type': 'ir.actions.act_window', 'res_model': 'cod.reconciliation', 'res_id': OO000O00OO00O0000.id, 'view_mode': 'form', 'target': 'current'}