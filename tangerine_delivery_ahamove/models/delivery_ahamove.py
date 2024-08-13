# -*- coding: utf-8
import time
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import ustr
from odoo.addons.tangerine_delivery_base.settings.utils import standardization_e164, get_route_api, notification
from odoo.addons.tangerine_delivery_base.api.connection import Connection
from ..settings.constants import settings
from ..api.client import Client


class ProviderAhamove(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[
        ('ahamove', 'Ahamove')
    ], ondelete={'ahamove': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})

    ahamove_partner_phone = fields.Char(string='Phone')
    ahamove_service_request_domain = fields.Binary(default=[], store=False)
    default_ahamove_service_id = fields.Many2one('ahamove.service', string='Service Type')
    default_ahamove_service_request_ids = fields.Many2many(
        'ahamove.service.request',
        'delivery_request_rel',
        'delivery_id',
        'request_id',
        string='Request Type'
    )
    default_ahamove_payment_method = fields.Selection(selection=settings.payment_method.value, string='Payment Method')

    @api.onchange('default_ahamove_service_id')
    def _onchange_default_ahamove_service_id(self):
        for rec in self:
            if rec.default_ahamove_service_id:
                rec.ahamove_service_request_domain = [('service_id', '=', rec.default_ahamove_service_id.id)]

    def _ahamove_payload_get_token(self):
        return {
            'mobile': standardization_e164(self.ahamove_partner_phone),
            'api_key': self.api_key
        }

    def ahamove_get_access_token(self):
        self.ensure_one()
        try:
            if not self.ahamove_partner_phone:
                raise UserError(_('The field phone is required'))
            elif not self.api_key:
                raise UserError(_('The field API key is required'))
            client = Client(Connection(self, get_route_api(self, settings.get_token_route_code.value)))
            result = client.get_access_token(self._ahamove_payload_get_token())
            self.write({
                'access_token': result.get('token'),
                'refresh_token': result.get('refresh_token')
            })
            return notification('success', 'Get access token successfully')
        except Exception as e:
            raise UserError(_(ustr(e)))

    def _ahamove_param_estimate_order(self, order):
        warehouse_id = order.warehouse_id
        ahamove_service = order.env.context.get('ahamove_service')
        ahamove_service_request_ids = order.env.context.get('ahamove_service_request_ids')
        promo_code = order.env.context.get('promo_code')
        if not warehouse_id:
            raise UserError(_('The warehouse is required on sale order'))
        elif not warehouse_id.partner_id.state_id.ahamove_city_code:
            raise UserError(_('The ahamove code is not set on warehouse address'))
        elif not ahamove_service:
            ahamove_service = f'{warehouse_id.partner_id.state_id.ahamove_city_code}-BIKE'
        payload = {
            'token': self.access_token,
            'service_id': ahamove_service,
            'items': [{
                'name': line.product_id.name,
                'num': int(line.product_uom_qty),
                'price': line.price_subtotal
            } for line in order.order_line if not line.is_delivery],
            'path': [
                {'address': warehouse_id.partner_id.shipping_address},
                {'address': order.partner_shipping_id.shipping_address}
            ],
            'order_time': 0
        }
        if promo_code:
            payload.update({'promo_code': promo_code})
        if ahamove_service_request_ids:
            requests = []
            for request_id in ahamove_service_request_ids:
                request = {'_id': request_id.code}
                if request_id.type_of_request == settings.request_group_bulky.value:
                    request.update({'tier_code': settings.default_tier.value})
                elif request_id.type_of_request == settings.request_group_tip.value:
                    request.update({'num': 1})
                requests.append(request)
            if requests:
                payload.update({'requests': requests})
        return payload

    def ahamove_rate_shipment(self, order):
        client = Client(Connection(self, get_route_api(self, settings.estimate_order_route_code.value)))
        result = client.estimate_order_fee(self._ahamove_param_estimate_order(order))
        return {
            'success': True,
            'price': result.get('total_price'),
            'error_message': False,
            'warning_message': False
        }

    def _ahamove_param_create_order(self, picking):
        sender_id = picking.picking_type_id.warehouse_id.partner_id
        payload = {
            'token': self.access_token,
            'order_time': 0,
            'path': [
                {
                    'address': sender_id.shipping_address,
                    'name': sender_id.name,
                    'mobile': standardization_e164(sender_id.mobile or sender_id.phone),
                    'tracking_number': picking.name
                },
                {
                    'address': picking.partner_id.shipping_address,
                    'name': picking.partner_id.name,
                    'mobile': standardization_e164(picking.partner_id.mobile or picking.partner_id.phone)
                },
            ],
            'service_id': picking.ahamove_service_id.code,
            'payment_method': picking.ahamove_payment_method,
            'items': [
                {
                    '_id': line.product_id.id,
                    'num': line.quantity,
                    'name': line.product_id.name,
                    'price': line.product_id.list_price * line.quantity
                } for line in picking.move_ids_without_package
            ]
        }
        if picking.cash_on_delivery and picking.cash_on_delivery_amount > 0.0:
            payload['path'][1]['cod'] = picking.cash_on_delivery_amount
        if picking.schedule_order:
            payload['order_time'] = int(time.mktime(picking.schedule_pickup_time_to.timetuple()))
            payload['idle_until'] = int(time.mktime(picking.schedule_pickup_time_to.timetuple()))
        if picking.remarks:
            payload['remarks'] = picking.remarks
        if picking.promo_code:
            payload['promo_code'] = picking.promo_code
        if picking.ahamove_service_request_ids:
            requests = []
            for request_id in picking.ahamove_service_request_ids:
                request = {'_id': request_id.code}
                if request_id.type_of_request == settings.request_group_bulky.value:
                    request.update({'tier_code': settings.default_tier.value})
                elif request_id.type_of_request == settings.request_group_tip.value:
                    request.update({'num': 1})
                requests.append(request)
            if requests:
                payload.update({'requests': requests})
        return payload

    def ahamove_send_shipping(self, pickings):
        client = Client(Connection(self, get_route_api(self, settings.create_order_route_code.value)))
        for picking in pickings:
            result = client.create_order(self._ahamove_param_create_order(picking))
            status_id = self.env.ref(
                'tangerine_delivery_ahamove.ahamove_idle_status') if picking.schedule_order else self.env.ref(
                'tangerine_delivery_ahamove.ahamove_assigning_status')
            picking.write({'delivery_status_id': status_id.id if status_id else False})
            self.env['carrier.ref.order'].sudo().create({'picking_id': picking.id})
            return [{
                'exact_price': result.get('order').get('total_price'),
                'tracking_number': result.get('order_id')
            }]

    def _ahamove_param_cancel_shipment(self, order):
        return {
            'token': self.access_token,
            'order_id': order,
            'comment': settings.cancel_reason.value,
            'cancel_code': settings.cancel_reason_code.value
        }

    def ahamove_cancel_shipment(self, picking):
        client = Client(Connection(self, get_route_api(self, settings.cancel_order_route_code.value)))
        client.cancel_order(self._ahamove_param_cancel_shipment(picking.carrier_tracking_ref))
        picking.write({
            'carrier_tracking_ref': False,
            'carrier_price': 0.0,
            'delivery_status_id': False
        })
        return notification(
            'success',
            f'Cancel tracking reference {picking.carrier_tracking_ref} successfully'
        )

    def ahamove_toggle_prod_environment(self):
        self.ensure_one()
        if self.prod_environment:
            self.domain = settings.domain_production.value
        else:
            self.domain = settings.domain_staging.value

    @staticmethod
    def ahamove_get_tracking_link(picking):
        return picking.ahamove_shared_link
