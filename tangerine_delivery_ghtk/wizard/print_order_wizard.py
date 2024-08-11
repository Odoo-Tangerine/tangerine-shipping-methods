from odoo import fields, models
from ..settings.constants import settings


class PrintOrderWizard(models.TransientModel):
    _inherit = 'print.order.wizard'

    ghtk_paper_size = fields.Selection(
        selection=settings.paper_size.value,
        string='Paper Type',
        default='A5',
    )
    ghtk_print_layout = fields.Selection(
        selection=settings.print_layouts.value,
        string='Layout',
        default='landscape',
    )

    def ghtk_print_order(self):
        return self.picking_id.carrier_id.ghtk_print_order(
            self.picking_id,
            self.ghtk_print_layout,
            self.ghtk_paper_size,
        )
