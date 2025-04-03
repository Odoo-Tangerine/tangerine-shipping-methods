import json
from odoo import models, fields, api
from ..settings.constants import settings

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        if self.group_id.sale_id and self.group_id.sale_id.carrier_id.delivery_type == settings.code.value:
            delivery_line_ids = self.group_id.sale_id.order_line.filtered('is_delivery')
            if delivery_line_ids:
                delivery_line_id = delivery_line_ids[-1]
                if delivery_line_id.viettelpost_quotation_data:
                    data = json.loads(delivery_line_id.viettelpost_quotation_data)
                    vals['viettelpost_service_id'] = data.get('viettelpost_service_id')
                    vals['viettelpost_service_extend_id'] = data.get('viettelpost_service_extend_id', False)
                    vals['cash_on_delivery'] = data.get('viettelpost_cod')
                    vals['cash_on_delivery_amount'] = data.get('viettelpost_cod_amount')
                    vals['viettelpost_national_type'] = data.get('viettelpost_national_type')
                    vals['viettelpost_product_type'] = data.get('viettelpost_product_type')
        return vals
