import json
from odoo import models, fields, api
from ..settings.constants import settings

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        if self.group_id.sale_id and self.group_id.sale_id.carrier_id.delivery_type == settings.ahamove_code.value:
            delivery_line_ids = self.group_id.sale_id.order_line.filtered('is_delivery')
            if delivery_line_ids:
                delivery_line_id = delivery_line_ids[-1]
                if delivery_line_id.ahamove_quotation_data:
                    data = json.loads(delivery_line_id.ahamove_quotation_data)
                    vals['ahamove_service_id'] = data.get('ahamove_service_id')
                    vals['ahamove_service_request_ids'] = data.get('ahamove_service_request_ids')
                    vals['cash_on_delivery'] = data.get('ahamove_cod')
                    vals['cash_on_delivery_amount'] = data.get('ahamove_cod_amount')
                    vals['promo_code'] = data.get('promo_code')
        return vals