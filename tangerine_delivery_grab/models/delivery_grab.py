# -*- coding: utf-8 -*-
import re
import time
import math
import threading
from datetime import datetime, timedelta
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import ustr
from odoo.addons.tangerine_delivery_base.settings.utils import (
    datetime_to_rfc3339,
    standardization_e164,
    get_route_api,
    notification
)
from odoo.addons.tangerine_delivery_base.api.connection import Connection
from ..settings.constants import settings
from ..api.client import Client


class ProviderGrab(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[
        ('grab', 'Grab Express')
    ], ondelete={'grab': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})

    default_grab_location_mode = fields.Selection(selection=settings.location_mode.value, string='Location Mode')
    default_grab_payer = fields.Selection(selection=settings.payer.value, string='Payer')
    default_grab_service_type = fields.Selection(selection=settings.service_type.value, string='Service Type')
    default_grab_vehicle_type = fields.Selection(selection=settings.vehicle_type.value, string='Vehicle Type')
    default_grab_payment_method = fields.Selection(selection=settings.payment_method.value, string='Payment Method')

    @staticmethod
    def _compute_expires_seconds_to_datetime(expires_times):
        return datetime.now() + timedelta(seconds=expires_times)

    def _update_cron_refresh_token(self, expires_times):
        time.sleep(10)
        with self.pool.cursor() as new_cr:
            self = self.with_env(self.env(cr=new_cr))
            cron = self.env.ref('tangerine_delivery_grab.ir_cron_refresh_access_token_grab', raise_if_not_found=False)
            if cron:
                cron.sudo().write({
                    'nextcall': datetime.now() + timedelta(seconds=expires_times),
                    'active': True
                })

    def grab_get_access_token(self):
        try:
            self.ensure_one()
            if not self.client_id:
                raise UserError(_('The field ClientID is required'))
            elif not self.client_secret:
                raise UserError(_('The field Client Secret is required'))
            elif not self.grant_type:
                raise UserError(_('The field Grant Type is required'))
            elif not self.scope:
                raise UserError(_('The field Scope is required'))
            client = Client(Connection(self, get_route_api(self, settings.oauth_route_code.value)))
            result = client.get_access_token({
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': self.grant_type,
                'scope': self.scope
            })
            self.write({
                'token_type': result.get('token_type'),
                'access_token': result.get('access_token'),
                'expire_token_date': self._compute_expires_seconds_to_datetime(result.get('expires_in'))
            })
            threaded_update_cron = threading.Thread(target=lambda: self._update_cron_refresh_token(int(result.get('expires_in'))))
            threaded_update_cron.start()
            return notification('success', 'Get access token successfully')
        except Exception as e:
            raise UserError(ustr(e))

    @staticmethod
    def _grab_validate_coordinates(contact):
        lat_pattern = re.compile(r"^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?)$")
        lng_pattern = re.compile(r"^[-+]?((1[0-7]\d(\.\d+)?|180(\.0+)?)|([1-9]?\d(\.\d+)?))$")
        if not bool(lat_pattern.match(str(contact.partner_latitude))):
            raise ValidationError(
                _(f'The Latitude of contact: {contact.name} incorrect - Value: {contact.partner_latitude}'))
        if not bool(lng_pattern.match(str(contact.partner_longitude))):
            raise ValidationError(
                _(f'The Longitude of contact: {contact.name} incorrect - Value: {contact.partner_latitude}'))
        return contact.partner_latitude, contact.partner_longitude

    def _grab_building_address(self, contact):
        if self.default_grab_location_mode == settings.coordinates_mode.value:
            base_geo_module_installed = self.env['ir.module.module'].sudo().search([
                ('name', '=', 'base_geolocalize'),
                ('state', '=', 'installed')
            ])
            if not base_geo_module_installed:
                raise UserError(_('Please install the module Partners Geolocation'))
            lat, lng = self._grab_validate_coordinates(contact)
            return {
                'address': contact.shipping_address_international,
                'coordinates': {
                    'latitude': lat,
                    'longitude': lng
                }
            }
        if not contact.state_id.grab_city_code:
            raise ValidationError(_(f'The Grab city code field of contact {contact.name} is required'))
        return {
            'address': contact.shipping_address_international,
            'cityCode': contact.state_id.grab_city_code,
            'coordinates': {}
        }

    def _grab_get_packages(self, line_ids):
        packages = []
        for line in line_ids:
            if hasattr(line, 'quantity'):
                packages.append({
                    'name': line.name,
                    'description': line.name,
                    'quantity': int(line.quantity) if hasattr(line, 'quantity') else int(line.product_uom_qty),
                    'dimensions': {
                        'height': 0,
                        'width': 0,
                        'depth': 0,
                        'weight': math.ceil(self.convert_weight(line.product_id.weight, self.base_weight_unit))
                    }
                })
            else:
                if not line.is_delivery:
                    packages.append({
                        'name': line.name,
                        'description': line.name,
                        'quantity': int(line.quantity) if hasattr(line, 'quantity') else int(line.product_uom_qty),
                        'dimensions': {
                            'height': 0,
                            'width': 0,
                            'depth': 0,
                            'weight': math.ceil(self.convert_weight(line.product_id.weight, self.base_weight_unit))
                        }
                    })
        return packages

    def _grab_payload_delivery_quotes(self, order):
        payload = {
            'origin': self._grab_building_address(order.warehouse_id.partner_id),
            'destination': self._grab_building_address(order.partner_shipping_id),
            'packages': self._grab_get_packages(order.order_line)
        }
        if order.env.context.get('grab_service_type'):
            payload.update({'serviceType': order.env.context.get('grab_service_type')})
        if order.env.context.get('grab_vehicle_type'):
            payload.update({'vehicleType': order.env.context.get('grab_vehicle_type')})
        if order.env.context.get('grab_cod') and order.env.context.get('grab_cod_amount', 0) > 0:
            payload.update({'cashOnDelivery': {'amount': order.env.context.get('grab_cod_amount')}})
        return payload

    def grab_rate_shipment(self, order):
        client = Client(Connection(self, get_route_api(self, settings.get_quotes_route_code.value)))
        result = client.get_delivery_quotes(payload=self._grab_payload_delivery_quotes(order))
        return {
            'success': True,
            'price': result.get('quotes')[0].get('amount'),
            'error_message': False,
            'warning_message': False
        }

    @staticmethod
    def _validate_picking(picking):
        if picking.promo_code and not picking.grab_payment_method:
            raise UserError(_('You are using a promo code, please select a payment method. This is required.'))
        elif picking.grab_payer == 'RECIPIENT' and picking.grab_payment_method == 'CASHLESS':
            raise UserError(_('Sending a RECIPIENT value for CASHLESS payments will result in an error.'))
        elif picking.cash_on_delivery and picking.cash_on_delivery_amount <= 0.0:
            raise UserError(_('The cash on delivery amount must be greater than 0.'))
        elif picking.schedule_order and not picking.schedule_pickup_time_from:
            raise UserError(_('You are using Scheduled for Order. Please select the pickup time from.'))
        elif picking.schedule_order and not picking.schedule_pickup_time_to:
            raise UserError(_('You are using Scheduled for Order. Please select the pickup time to.'))
        elif picking.schedule_order and (picking.schedule_pickup_time_from >= picking.schedule_pickup_time_to):
            raise UserError(_('The delivery time in the future must be greater than the present time.'))

    def _grab_payload_create_delivery_request(self, picking):
        self._validate_picking(picking)
        sender_id = picking.picking_type_id.warehouse_id.partner_id
        payload = {
            'merchantOrderID': picking.origin,
            'serviceType': picking.grab_service_type,
            'vehicleType': picking.grab_vehicle_type,
            'codType': picking.grab_cod_type or '',
            'paymentMethod': picking.grab_payment_method,
            'payer': picking.grab_payer,
            'highValue': picking.grab_high_value,
            'packages': self._grab_get_packages(picking.move_ids_without_package),
            'sender': {
                'firstName': sender_id.name,
                'phone': standardization_e164(sender_id.phone or sender_id.mobile)
            },
            'recipient': {
                'firstName': picking.partner_id.name,
                'phone': standardization_e164(picking.partner_id.phone or picking.partner_id.mobile)
            },
            'origin': self._grab_building_address(sender_id),
            'destination': self._grab_building_address(picking.partner_id),
        }
        if picking.cash_on_delivery:
            payload.update({'cashOnDelivery': {'amount': picking.cash_on_delivery_amount}})
        if picking.schedule_order:
            payload.update({
                'schedule': {
                    'pickupTimeFrom': datetime_to_rfc3339(picking.schedule_pickup_time_from, picking.env.user.tz),
                    'pickupTimeTo': datetime_to_rfc3339(picking.schedule_pickup_time_to, picking.env.user.tz)
                }
            })
        return payload

    @staticmethod
    def _grab_payload_carrier_ref_order(picking):
        return {
            'grab_service_type': picking.grab_service_type,
            'grab_vehicle_type': picking.grab_vehicle_type,
            'grab_payment_method': picking.grab_payment_method,
            'grab_payer': picking.grab_payer,
            'grab_cod_type': picking.grab_cod_type,
            'grab_high_value': picking.grab_high_value
        }

    def grab_send_shipping(self, pickings):
        client = Client(Connection(self, get_route_api(self, settings.create_request_route_code.value)))
        for picking in pickings:
            ref_id = self.env['carrier.ref.order'].search([('picking_id', '=', picking.id)])
            if ref_id and ref_id.delivery_status_id.code not in settings.allow_booking_status.value:
                raise UserError(_(f'This delivery note has already been placed. Please do not place a new order.'))
            result = client.create_delivery_request(self._grab_payload_create_delivery_request(picking))
            status_id = self.env.ref('tangerine_delivery_grab.grab_status_queueing') if picking.schedule_order else self.env.ref('tangerine_delivery_grab.grab_status_allocating')
            picking.write({'delivery_status_id': status_id.id if status_id else False})
            self.env['carrier.ref.order'].create({
                **self.common_payload_carrier_ref_order(
                    picking,
                    status_id,
                    result.get('quote').get('amount'),
                    result.get('deliveryID')
                ),
                **self._grab_payload_carrier_ref_order(picking)
            })
            return [{
                'exact_price': result.get('quote').get('amount'),
                'tracking_number': result.get('deliveryID')
            }]

    @staticmethod
    def grab_get_tracking_link(picking):
        return picking.grab_tracking_link

    def grab_cancel_shipment(self, picking):
        if picking.delivery_status_id.code in settings.list_status_cancellation_allowed.value:
            raise UserError(_(f'You cannot cancel while the order is in {picking.delivery_status_id.name} status'))
        client = Client(Connection(self, get_route_api(self, settings.cancel_request_route_code.value)))
        client.cancel_delivery(picking.carrier_tracking_ref)
        picking.write({'carrier_tracking_ref': False, 'carrier_price': 0.0, 'delivery_status_id': False})
        return notification('success', f'Cancel tracking reference {picking.carrier_tracking_ref} successfully')

    def grab_toggle_prod_environment(self):
        self.ensure_one()
        data = []
        for route_id in self.route_api_ids:
            item = route_id.route.split('/')
            if item[1] == 'grabid': continue
            item[1] = settings.production_route.value if self.prod_environment else settings.staging_route.value
            data.append((1, route_id.id, {'route': '/'.join(item)}))
        if data:
            self.write({'route_api_ids': data})

    def _grab_get_default_custom_package_code(self):...
