# -*- coding: utf-8 -*-
import math
import pytz
import time
import threading
from dateutil import parser
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import ustr
from odoo.addons.tangerine_delivery_base.settings.utils import (
    get_route_api,
    notification,
    convert_e164_to_classic
)
from odoo.addons.tangerine_delivery_base.api.connection import Connection
from ..settings.constants import settings
from ..api.client import Client


class ProviderViettelpost(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[
        ('express_247', '247 Express')
    ], ondelete={'express_247': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})
    default_express_247_service_type_id = fields.Many2one(
        'service.type.247.express',
        string='Service Type'
    )
    default_express_247_special_service_type_ids = fields.Many2many(
        'special.service.type.247.express',
        string='Special Service Type'
    )
    default_express_247_product_type = fields.Selection(settings.product_type.value, string='Product Type')

    @staticmethod
    def _express_247_calculate_expire_date(expire_date):
        return parser.isoparse(expire_date).astimezone(pytz.utc).replace(tzinfo=None)

    def express_247_get_access_token(self):
        try:
            self.ensure_one()
            if not self.username:
                raise ValidationError(_('The field Username is required'))
            elif not self.password:
                raise ValidationError(_('The field Password is required'))
            client = Client(Connection(self, get_route_api(self, settings.get_access_token_route_code.value)))
            result = client.get_access_token({
                'UserName': self.username,
                'Password': self.password
            })
            expire_date = self._express_247_calculate_expire_date(result.get('ExpireDate'))
            self.write({
                'access_token': result.get('Token'),
                'client_id': result.get('ClientID'),
                'api_key': result.get('TrackingApiKey'),
                'expire_token_date': expire_date
            })
            self.env['service.type.247.express'].express_247_service_type_synchronous()
            self.env['special.service.type.247.express'].express_247_special_service_type_synchronous()
            return notification('success', 'Get access token successfully')
        except Exception as e:
            raise UserError(ustr(e))

    def _express_247_payload_get_price(self, order):
        warehouse_id = order.warehouse_id
        if not warehouse_id:
            raise ValidationError(_('The warehouse is required on sale order'))
        if not order.env.context.get('express_247_service_type'):
            raise ValidationError(_('The field service type is required'))
        return {
            'ToProvinceName': order.partner_shipping_id.state_id.name,
            'ToDistrictName': order.partner_shipping_id.district_id.name,
            'ToWardName': order.partner_shipping_id.ward_id.name,
            'Length': 0,
            'Width': 0,
            'Height': 0,
            'RealWeight': math.ceil(self.convert_weight(order._get_estimated_weight(), self.base_weight_unit)),
            'ClientHubID': warehouse_id.express_247_hub_id,
            'ServiceTypeID': order.env.context.get('express_247_service_type')
        }

    def express_247_rate_shipment(self, order):
        client = Client(Connection(self, get_route_api(self, settings.get_price_route_code.value)))
        result = client.get_price(self._express_247_payload_get_price(order))
        return {
            'success': True,
            'price': result.get('TotalServiceCost'),
            'error_message': False,
            'warning_message': False
        }

    def _express_247_payload_create_order(self, picking):
        warehouse_id = picking.picking_type_id.warehouse_id
        payload = {
            'OrderInfo': {
                'ClientHubID': warehouse_id.express_247_hub_id,
                'ContactName': warehouse_id.partner_id.name,
                'ContactPhone': convert_e164_to_classic(warehouse_id.partner_id.phone or warehouse_id.partner_id.mobile),
                'SenderAddress': warehouse_id.partner_id.shipping_address,
                'ReceiverPhone': convert_e164_to_classic(picking.partner_id.phone or picking.partner_id.mobile),
                'ReceiverName': picking.partner_id.name,
                'ReceiverAddress': picking.partner_id.shipping_address,
                'ReceiverProvinceName': picking.partner_id.state_id.name,
                'ReceiverDistrictName': picking.partner_id.district_id.name,
                'ReceiverWardName': picking.partner_id.ward_id.name,
                'Length': 0,
                'Width': 0,
                'Height': 0,
                'RealWeight': math.ceil(self.convert_weight(picking._get_estimated_weight(), self.base_weight_unit)),
                'Quantity': 1,
                'Note': picking.remarks or '',
                'ServiceTypeID': picking.express_247_service_type_id.code,
                'MailerType': picking.express_247_product_type,
                'ExternalCode': picking.name,
                'ReferenceCode': picking.sale_id.name,
                'InformFee': str(int(picking.sale_id.amount_total)),
                'Items': [{
                    'No': i,
                    'ItemID': rec.product_id.default_code or rec.product_id.name,
                    'ItemName': rec.product_id.name,
                    'UnitName': 'Unit',
                    'Qty': int(rec.quantity),
                    'UnitPrice': int(rec.product_id.lst_price),
                    'Amount': int(rec.product_id.lst_price * rec.quantity)
                } for i, rec in enumerate(picking.move_line_ids, start=1)],
            }
        }
        if picking.cash_on_delivery:
            payload['CODAmount'] = picking.cash_on_delivery_amount
            payload['SpecialInstructionId'] = picking.express_247_is_inspection_goods_allowed
        if picking.express_247_special_service_type_ids:
            payload['ExtraServices'] = [rec.code for rec in picking.express_247_special_service_type_ids]
        return payload

    @staticmethod
    def _express_247_payload_carrier_ref_order(picking):
        return {
            'express_247_is_inspection_goods_allowed': picking.express_247_is_inspection_goods_allowed,
            'express_247_service_type_id': picking.express_247_service_type_id.id,
            'express_247_special_service_type_ids': picking.express_247_special_service_type_ids.ids,
            'express_247_product_type': picking.express_247_product_type,
        }

    def express_247_send_shipping(self, pickings):
        for picking in pickings:
            client = Client(Connection(self, get_route_api(self, settings.create_order_route_code.value)))
            result = client.create_order(self._express_247_payload_create_order(picking))
            if not result.get('OrderInfo'):
                raise UserError(_(f'Failed to create order'))
            order_info = result.get('OrderInfo')
            status_id = self.env.ref('tangerine_delivery_express_247.247_express_status_datiepnhan')
            picking.write({'delivery_status_id': status_id.id if status_id else False})
            self.env['carrier.ref.order'].create({
                **self.common_payload_carrier_ref_order(
                    picking,
                    status_id,
                    order_info.get('TotalServiceCost'),
                    order_info.get('OrderCode')
                ),
                **self._express_247_payload_carrier_ref_order(picking)
            })
            return [{
                'exact_price': order_info.get('TotalServiceCost'),
                'tracking_number': order_info.get('OrderCode')
            }]

    def express_247_get_tracking_link(self, picking):
        raise UserError(_('247 Express does not support tracking link. Please use the tracking number instead.'))

    def express_247_toggle_prod_environment(self):
        self.ensure_one()
        if self.prod_environment:
            self.domain = settings.domain_production.value
        else:
            self.domain = settings.domain_staging.value

    def express_247_cancel_shipment(self, picking):
        client = Client(Connection(self, get_route_api(self, settings.cancel_order_code.value)))
        client.cancel_order({'OrderCode': picking.carrier_tracking_ref,})
        picking.write({'carrier_tracking_ref': False, 'carrier_price': 0.0, 'delivery_status_id': False})
        return notification('success', 'Cancel tracking reference successfully')