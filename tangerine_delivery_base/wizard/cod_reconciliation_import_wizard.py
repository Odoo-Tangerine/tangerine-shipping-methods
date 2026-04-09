# -*- coding: utf-8 -*-
import base64
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CodReconciliationImportWizard(models.TransientModel):
    _name = 'cod.reconciliation.import.wizard'
    _description = 'COD Reconciliation Import Wizard'

    reconciliation_id = fields.Many2one(
        'cod.reconciliation',
        string='Reconciliation',
    )
    carrier_id = fields.Many2one(
        'delivery.carrier',
        string='Carrier',
        required=True,
        domain="[('is_support_auto_cod_reconciliation', '=', True)]",
    )
    delivery_type = fields.Selection(
        related='carrier_id.delivery_type',
    )
    import_file = fields.Binary(string='Import File', required=True)
    import_filename = fields.Char(string='Filename')
    auto_reconcile = fields.Boolean(
        string='Auto Reconcile After Import',
        default=True,
        help='Automatically start reconciliation after importing the file.',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'carrier_id' in fields_list and not res.get('carrier_id'):
            reconciliation_id = res.get('reconciliation_id') or self.env.context.get('default_reconciliation_id')
            if reconciliation_id:
                reconciliation = self.env['cod.reconciliation'].browse(reconciliation_id)
                if reconciliation.carrier_id:
                    res['carrier_id'] = reconciliation.carrier_id.id
        return res

    def action_import(self):
        """Import the file and create reconciliation lines."""
        self.ensure_one()

        if not self.import_file:
            raise UserError(_('Please select a file to import.'))

        # Create reconciliation record if not provided
        reconciliation = self.reconciliation_id
        if not reconciliation:
            reconciliation = self.env['cod.reconciliation'].create({
                'carrier_id': self.carrier_id.id,
            })

        if reconciliation.state not in ('draft', 'imported'):
            raise UserError(_('Can only import into Draft or Imported state.'))

        # Clear existing lines
        reconciliation.line_ids.unlink()

        # Decode file
        file_data = base64.b64decode(self.import_file)

        # Call carrier-specific parser on the reconciliation model
        result = reconciliation._parse_reconciliation_file(file_data, self.import_filename)

        if not result or not result.get('lines'):
            raise UserError(_('No data lines found in the imported file.'))

        # Validate bill codes against system
        CarrierRef = self.env['carrier.ref.order']
        bill_codes = [line.get('carrier_bill_code') for line in result['lines'] if line.get('carrier_bill_code')]
        if bill_codes:
            existing_refs = CarrierRef.search([
                ('carrier_tracking_ref', 'in', bill_codes),
                ('company_id', '=', reconciliation.company_id.id),
            ]).mapped('carrier_tracking_ref')
            not_found_codes = [code for code in bill_codes if code not in existing_refs]
            if not_found_codes:
                raise UserError(_(
                    'The following %(count)s bill code(s) were not found in the system. '
                    'Import has been cancelled.\n\n%(codes)s',
                    count=len(not_found_codes),
                    codes=', '.join(not_found_codes),
                ))

        # Create lines
        line_vals = []
        for line in result['lines']:
            line['reconciliation_id'] = reconciliation.id
            line_vals.append(line)

        self.env['cod.reconciliation.line'].create(line_vals)

        # Update reconciliation record
        update_vals = {
            'state': 'imported',
            'import_date': fields.Datetime.now(),
            'import_file': self.import_file,
            'import_filename': self.import_filename,
            'carrier_id': self.carrier_id.id,
            'carrier_total_cod': result.get('carrier_total_cod', 0),
            'carrier_total_shipping_fee': result.get('carrier_total_shipping_fee', 0),
            'carrier_net_amount': result.get('carrier_net_amount', 0),
            'period_date': result.get('period_date', False),
        }

        # Allow carrier-specific extra fields
        for key, value in result.get('extra_vals', {}).items():
            update_vals[key] = value

        reconciliation.write(update_vals)

        reconciliation.message_post(
            body=_(
                'Imported %(count)s lines from file "%(filename)s". '
                'Carrier Total COD: %(cod)s, Carrier Total Fees: %(fees)s.',
                count=len(line_vals),
                filename=self.import_filename or 'N/A',
                cod=result.get('carrier_total_cod', 0),
                fees=result.get('carrier_total_shipping_fee', 0),
            ),
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )

        # Auto reconcile if requested
        if self.auto_reconcile:
            reconciliation.action_reconcile()

        # Open the created/updated reconciliation record
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cod.reconciliation',
            'res_id': reconciliation.id,
            'view_mode': 'form',
            'target': 'current',
        }
