import json
from odoo import models, fields, api
from ..settings.constants import settings

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        if self.group_id.sale_id and self.group_id.sale_id.carrier_id.delivery_type == settings.nhat_tin_code.value:
            delivery_line_ids = self.group_id.sale_id.order_line.filtered('is_delivery')
            if delivery_line_ids:
                delivery_line_id = delivery_line_ids[-1]
                if delivery_line_id.ntl_quotation_data:
                    data = json.loads(delivery_line_id.ntl_quotation_data)
                    vals['ntl_service_type'] = data.get('ntl_service_type')
                    vals['ntl_payment_method'] = data.get('ntl_payment_method')
                    vals['cash_on_delivery'] = data.get('ntl_cod')
                    vals['cash_on_delivery_amount'] = data.get('ntl_cod_amount')
        return vals
