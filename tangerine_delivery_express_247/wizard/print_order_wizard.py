from odoo import fields, models
from ..settings.constants import settings


class PrintOrderWizard(models.TransientModel):
    _inherit = 'print.order.wizard'

    viettelpost_paper_size = fields.Selection(
        selection=settings.paper_size.value,
        string='Paper Type',
        default='a5',
    )

    def viettelpost_print_order(self):
        return self.picking_id.carrier_id.viettelpost_print_order(self.carrier_tracking_ref, self.viettelpost_paper_size)