# -*- coding: utf-8 -*-
import json
import math
from datetime import datetime
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.addons.tangerine_delivery_base.settings.utils import (
    standardization_e164,
    get_route_api,
    notification,
    datetime_to_iso_8601,
    rfc3339_to_datetime
)
from odoo.addons.tangerine_delivery_base.api.connection import Connection
from ..settings.constants import settings
from ..api.client import Client


class ProviderGrab(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[
        ('lalamove', 'Lalamove')
    ], ondelete={'lalamove': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})

    lalamove_service_ids = fields.One2many('lalamove.service', 'carrier_id')
    lalamove_spec_service_ids = fields.One2many('lalamove.special.service', 'carrier_id')
    default_lalamove_regional_id = fields.Many2one('lalamove.regional', string='Regional', required=True)
    default_lalamove_service_id = fields.Many2one('lalamove.service', string='Service Type')
    lalamove_special_service_domain = fields.Binary(default=[], store=False)
    default_lalamove_special_service_ids = fields.Many2many(
        'lalamove.special.service',
        'lalamove_carrier_service_rel',
        'carrier_id',
        'special_id',
        string='Special Service'
    )

    def action_lalamove_sync_cities(self):
        self.env['lalamove.service'].llm_service_synchronous()

    def _llm_get_enum_weight(self, instance):
        total_weight = math.ceil(self.convert_weight(instance._get_estimated_weight(), self.base_weight_unit))
        if total_weight < 10:
            weight_enum = settings.weight_lt_10.value
        elif 10 <= total_weight < 30:
            weight_enum = settings.weight_bw_10_30.value
        else:
            weight_enum = settings.weight_bw_30_50.value
        return weight_enum

    def _llm_payload_get_quotation_mode_order(self, order):
        warehouse_id = order.warehouse_id
        llm_service = order.env.context.get('llm_service')
        llm_special_service = order.env.context.get('llm_special_service')
        if not warehouse_id:
            raise UserError(_('The warehouse is required on sale order'))
        elif not llm_service:
            raise UserError(_('Lalamove Service is required'))
        payload = {
            'data': {
                'serviceType': llm_service,
                'language': self.default_lalamove_regional_id.lang,
                'stops': [
                    {'address': warehouse_id.partner_id.shipping_address},
                    {'address': order.partner_shipping_id.shipping_address}
                ],
                'item': {
                    'quantity': str(int(self._compute_quantity(order.order_line))),
                    'weight': self._llm_get_enum_weight(order)
                },
                'isRouteOptimized': False,
                }
            }
        if llm_special_service:
            payload['data']['specialRequests'] = llm_special_service
        return payload

    def lalamove_rate_shipment(self, order):
        client = Client(Connection(self, get_route_api(self, settings.llm_get_quotation_code.value)))
        result = client.get_quotation(self._llm_payload_get_quotation_mode_order(order))
        if result.get('priceBreakdown') and result.get('priceBreakdown').get('total'):
            return {
                'success': True,
                'price': result.get('priceBreakdown').get('total'),
                'error_message': False,
                'warning_message': False,
                'llm_quotation_data': json.dumps(result)
            }
        return {
            'success': False,
            'price': 0.0,
            'error_message': _('Error: Get rate shipment error.'),
            'warning_message': False
        }

    def _llm_payload_get_quotation_mode_picking(self, picking):
        sender_id = picking.picking_type_id.warehouse_id.partner_id
        recipient_id = picking.partner_id
        if not sender_id:
            raise UserError(_('The warehouse is required'))
        elif not recipient_id:
            raise UserError(_('The partner address is required'))
        elif not picking.lalamove_service_id and not picking.lalamove_got_quotation:
            raise UserError(_('Lalamove Service is required'))
        payload = {
            'data': {
                'serviceType': picking.lalamove_service_id.code,
                'language': self.default_lalamove_regional_id.lang,
                'stops': [
                    {'address': sender_id.shipping_address},
                    {'address': recipient_id.shipping_address}
                ],
                'item': {
                    'quantity': str(int(self._compute_quantity(picking.move_ids_without_package))),
                    'weight': self._llm_get_enum_weight(picking)
                },
                'isRouteOptimized': False,
                }
            }
        if picking.lalamove_special_service_ids:
            payload['data']['specialRequests'] = [rec.code for rec in picking.lalamove_special_service_ids]
        if picking.schedule_order:
            payload['data']['scheduleAt'] = datetime_to_iso_8601(picking.schedule_pickup_time_to)
        if picking.is_lalamove_goods_fragile:
            payload['data']['item']['handlingInstructions'] = ['FRAGILE_OR_HANDLE_WITH_CARE_']
        return payload

    def _llm_payload_place_order(self, picking):
        line_delivery = picking.sale_id.order_line.filtered(lambda l: l.lalamove_quotation_data)
        client = Client(Connection(self, get_route_api(self, settings.llm_get_quotation_code.value)))
        if not line_delivery:
            quotation_data = client.get_quotation(self._llm_payload_get_quotation_mode_picking(picking))
        else:
            quotation_data = json.loads(line_delivery[-1].lalamove_quotation_data)
            if quotation_data and rfc3339_to_datetime(quotation_data.get('expiresAt')) < datetime.now():
                quotation_data = client.get_quotation(self._llm_payload_get_quotation_mode_picking(picking))
        sender_id = picking.picking_type_id.warehouse_id.partner_id
        return {
            'data': {
                'quotationId': quotation_data.get('quotationId'),
                'sender': {
                    'stopId': quotation_data.get('stops')[0].get('stopId'),
                    'name': sender_id.name,
                    'phone': f'+{standardization_e164(sender_id.mobile or sender_id.phone)}',
                },
                'recipients': [
                    {
                        'stopId': quotation_data.get('stops')[1].get('stopId'),
                        'name': picking.partner_id.name,
                        'phone': f'+{standardization_e164(picking.partner_id.mobile or picking.partner_id.phone)}',
                        'remarks': picking.remarks or ''
                    }
                ],
                'isPODEnabled': False
            }
        }

    @staticmethod
    def _lalamove_payload_carrier_ref_order(picking):
        return {
            'is_lalamove_goods_fragile': picking.is_lalamove_goods_fragile,
            'lalamove_service_id': picking.lalamove_service_id.id,
            'lalamove_special_service_ids': picking.lalamove_special_service_ids.ids
        }

    def lalamove_send_shipping(self, pickings):
        client = Client(Connection(self, get_route_api(self, settings.llm_place_order_code.value)))
        for picking in pickings:
            ref_id = self.env['carrier.ref.order'].search([('picking_id', '=', picking.id)])
            if ref_id and ref_id.delivery_status_id.code not in settings.allow_booking_status.value:
                raise UserError(_(f'This delivery note has already been placed. Please do not place a new order.'))
            result = client.place_order(self._llm_payload_place_order(picking))
            status_id = self.env.ref('tangerine_delivery_lalamove.lalamove_status_assigning_driver')
            picking.write({
                'delivery_status_id': status_id.id if status_id else False,
                'lalamove_tracking_link': result.get('shareLink')
            })
            self.env['carrier.ref.order'].create({
                **self.common_payload_carrier_ref_order(
                    picking,
                    status_id,
                    float(result.get('priceBreakdown').get('total')),
                    result.get('orderId')
                ),
                **self._lalamove_payload_carrier_ref_order(picking)
            })
            return [{
                'exact_price': float(result.get('priceBreakdown').get('total')),
                'tracking_number': result.get('orderId')
            }]

    def lalamove_cancel_shipment(self, picking):
        client = Client(Connection(self, get_route_api(self, settings.llm_cancel_order_code.value)))
        client.cancel_order(picking.carrier_tracking_ref)
        picking.write({'carrier_tracking_ref': False, 'carrier_price': 0.0, 'delivery_status_id': False})
        return notification('success', f'Cancel tracking reference {picking.carrier_tracking_ref} successfully')

    @staticmethod
    def lalamove_get_tracking_link(picking):
        return picking.lalamove_tracking_link

    def lalamove_toggle_prod_environment(self):
        self.ensure_one()
        if self.prod_environment:
            self.domain = settings.domain_production.value
        else:
            self.domain = settings.domain_staging.value

    def _llm_payload_update_webhook(self):
        return {
            'data': {
                'url': self.webhook_url if not self.is_use_authentication else f'{self.webhook_url}/{self.webhook_access_token}'
            }
        }

    def action_lalamove_update_webhook(self):
        client = Client(Connection(self, get_route_api(self, settings.llm_register_webhook.value)))
        client.register_webhook(self._llm_payload_update_webhook())
        self.is_webhook_registered = bool(self.is_webhook_registered)
        return notification('success', 'Lalamove webhook registered')
