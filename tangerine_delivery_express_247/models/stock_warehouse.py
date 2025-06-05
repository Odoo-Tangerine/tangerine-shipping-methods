from odoo import fields, models
from odoo.addons.tangerine_delivery_base.settings.utils import (
    get_route_api,
    convert_e164_to_classic,
    notification
)
from ..settings.constants import settings
from odoo.addons.tangerine_delivery_base.api.connection import Connection
from ..api.client import Client


class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    express_247_hub_id = fields.Integer(string='HubID', readonly=True)

    @staticmethod
    def _247_express_payload_create_hub(warehouse):
        return {
            'HubInfo': {
                'Address': warehouse.partner_id.shipping_address,
                'ContactName': warehouse.partner_id.name,
                'ContactPhone': convert_e164_to_classic(warehouse.partner_id.phone or warehouse.partner_id.mobile),
                'DistrictName': warehouse.partner_id.district_id.name,
                'ProvinceName': warehouse.partner_id.state_id.name,
                'WardName': warehouse.partner_id.ward_id.name,
                'CusWarehouseID': warehouse.code,
                'CusWarehouseName': warehouse.name,
            }
        }

    def express_247_register_warehouse(self):
        for warehouse in self:
            carrier_id = warehouse.env['delivery.carrier'].search([('delivery_type', '=', settings.code.value)])
            client = Client(Connection(carrier_id, get_route_api(carrier_id, settings.create_hub_route_code.value)))
            result = client.create_hub(
                self._247_express_payload_create_hub(warehouse)
            )
            if result.get('HubInfo', {}) and result.get('HubInfo', {}).get('ClientHubID'):
                self.write({'express_247_hub_id': int(result.get('HubInfo', {}).get('ClientHubID'))})
                return notification('success', f'Register warehouse: {warehouse.name} successfully')
            return notification('danger', f'Register warehouse: {warehouse.name} error')
