# -*- coding: utf-8 -*-
import math
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.tangerine_delivery_base.settings.utils import (
    datetime_to_rfc3339,
    standardization_e164,
    get_route_api,
    notification
)
from odoo.addons.tangerine_delivery_base.api.connection import Connection
from ..settings.constants import settings
from ..api.client import Client


class ProviderNhatTinLogistics(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[
        ('nhat_tin', 'Nhat Tin Logistics')
    ], ondelete={'nhat_tin': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})

    ntl_partner_id = fields.Char(string='PartnerID')

    default_ntl_service_type = fields.Selection(selection=settings.service_type.value, string='Service Type')
    default_ntl_cargo_type = fields.Selection(selection=settings.cargo_type.value, string='Cargo Type')
    default_ntl_payment_method = fields.Selection(selection=settings.payment_method.value, string='Payment Method')

    def _nhat_tin_payload_calculate_price(self, order):
        if not order.env.context.get('ntl_service_type'):
            raise ValidationError(_('The field service type is required.'))
        elif not order.env.context.get('ntl_payment_method'):
            raise ValidationError(_('The field payment method is required.'))
        elif not order.warehouse_id.partner_id.state_id:
            raise ValidationError(_('The field sender province is required.'))
        elif not order.warehouse_id.partner_id.district_id:
            raise ValidationError(_('The field sender district is required.'))
        elif not order.partner_shipping_id.state_id:
            raise ValidationError(_('The field receiver province is required.'))
        elif not order.partner_shipping_id.district_id:
            raise ValidationError(_('The field receiver district is required.'))
        elif not self.ntl_partner_id:
            raise ValidationError(_('The field partner ID is required.'))
        weight = order._get_estimated_weight() or self.env.context.get('order_weight')
        payload = {
            'partner_id': int(self.ntl_partner_id),
            'weight': math.ceil(order.carrier_id.convert_weight(weight, self.base_weight_unit)),
            'service_id': int(order.env.context.get('ntl_service_type')),
            'payment_method_id': int(order.env.context.get('ntl_payment_method')),
            's_province': order.warehouse_id.partner_id.state_id.name,
            's_district': order.warehouse_id.partner_id.district_id.name,
            'r_province': order.partner_shipping_id.state_id.name,
            'r_district': order.partner_shipping_id.district_id.name,
            'cargo_value': self.env.context.get('ntl_cargo_value'),
        }
        if self.env.context.get('ntl_cod') and self.env.context.get('ntl_cod_amount', 0) > 0:
            payload['cod_amount'] = order.env.context.get('ntl_cod_amount')
        return payload

    def nhat_tin_rate_shipment(self, order):
        client = Client(Connection(self, get_route_api(self, settings.ntl_calculate_price_route_code.value)))
        result = client.calculate_price(payload=self._nhat_tin_payload_calculate_price(order))
        return {
            'success': True,
            'price': result.get('data')[0].get('total_fee'),
            'error_message': False,
            'warning_message': False
        }

    @staticmethod
    def _validate_payload_nhat_tin(picking):
        if not picking.ntl_service_type:
            raise ValidationError(_('The field service type is required.'))
        elif not picking.ntl_payment_method:
            raise ValidationError(_('The field payment method is required.'))
        elif not picking.ntl_cargo_type:
            raise ValidationError(_('The field cargo type is required.'))

    def _nhat_tin_payload_create_bill(self, picking):
        self._validate_payload_nhat_tin(picking)
        sender_id = picking.picking_type_id.warehouse_id.partner_id
        recipient_id = picking.partner_id
        payload = {
            'partner_id': int(self.ntl_partner_id),
            'ref_code': picking.sale_id.name,
            'weight': math.ceil(self.convert_weight(picking._get_estimated_weight(), self.base_weight_unit)),
            'service_id': int(picking.ntl_service_type),
            'payment_method_id': int(picking.ntl_payment_method),
            'note': picking.remarks or '',
            'cargo_type_id': int(picking.ntl_cargo_type),
            's_name': sender_id.name,
            's_phone': standardization_e164(sender_id.mobile or sender_id.phone),
            's_address': sender_id.shipping_address,
            's_ward_name': sender_id.ward_id.name,
            's_district_name': sender_id.district_id.name,
            's_province_name':sender_id.state_id.name,
            'r_name': recipient_id.name,
            'r_phone': standardization_e164(recipient_id.mobile or recipient_id.phone),
            'r_address': recipient_id.shipping_address,
            'r_ward_name': recipient_id.ward_id.name,
            'r_district_name': recipient_id.district_id.name,
            'r_province_name': recipient_id.state_id.name
        }
        if picking.cash_on_delivery and picking.cash_on_delivery_amount > 0.0:
            payload['cod_amount'] = picking.cash_on_delivery_amount
        return payload

    @staticmethod
    def _nhat_tin_payload_carrier_ref_order(picking):
        return {
            'ntl_service_type': picking.ntl_service_type,
            'ntl_payment_method': picking.ntl_payment_method,
            'ntl_cargo_type': picking.ntl_cargo_type,
        }

    def nhat_tin_send_shipping(self, pickings):
        client = Client(Connection(self, get_route_api(self, settings.ntl_create_bill_route_code.value)))
        for picking in pickings:
            result = client.create_bill(self._nhat_tin_payload_create_bill(picking))
            status_id = self.env.ref('tangerine_delivery_nhat_tin.ntl_status_2')
            picking.write({'delivery_status_id': status_id.id if status_id else False})
            self.env['carrier.ref.order'].create({
                **self.common_payload_carrier_ref_order(
                    picking,
                    status_id,
                    result.get('data').get('total_fee'),
                    result.get('data').get('bill_code')
                ),
                **self._nhat_tin_payload_carrier_ref_order(picking)
            })
            return [{
                'exact_price': result.get('data').get('total_fee'),
                'tracking_number': result.get('data').get('bill_code')
            }]

    @staticmethod
    def _nhat_tin_payload_cancel_bill(carrier_tracking_ref):
        return {'bill_code': [carrier_tracking_ref]}

    def nhat_tin_cancel_shipment(self, picking):
        client = Client(Connection(self, get_route_api(self, settings.ntl_cancel_bill_route_code.value)))
        client.cancel_bill(self._nhat_tin_payload_cancel_bill(picking.carrier_tracking_ref))
        picking.write({
            'carrier_tracking_ref': False,
            'carrier_price': 0.0,
            'delivery_status_id': False
        })
        return notification('success', 'Cancel tracking reference successfully')

    def nhat_tin_print_order(self, carrier_tracking_ref):
        if not self.domain_printer:
            raise UserError(_('The field domain printer is required.'))
        client = Client(Connection(self, get_route_api(self, settings.ntl_print_bill_route_code.value)))
        url = client.print_bill(carrier_tracking_ref)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def nhat_tin_toggle_prod_environment(self):
        self.ensure_one()
        if self.prod_environment:
            self.domain = settings.domain_production.value
            self.domain_printer = settings.domain_printer_production.value
        else:
            self.domain = settings.domain_staging.value
            self.domain_printer = settings.domain_printer_staging.value
