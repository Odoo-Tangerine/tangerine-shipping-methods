import json
from odoo import models, fields, api
from ..settings.constants import settings

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        if self.group_id.sale_id and self.group_id.sale_id.carrier_id.delivery_type == settings.grab_code.value:
            delivery_line_ids = self.group_id.sale_id.order_line.filtered('is_delivery')
            if delivery_line_ids:
                delivery_line_id = delivery_line_ids[-1]
                if delivery_line_id.grab_quotation_data:
                    data = json.loads(delivery_line_id.grab_quotation_data)
                    vals['grab_service_type'] = data.get('grab_service_type')
                    vals['grab_vehicle_type'] = data.get('grab_vehicle_type', False)
                    vals['cash_on_delivery'] = data.get('grab_cod')
                    vals['cash_on_delivery_amount'] = data.get('grab_cod_amount')
        return vals
