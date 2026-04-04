# -*- coding: utf-8 -*-
import hashlib
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from odoo.addons.tangerine_delivery_base.settings.utils import (
    standardization_e164,
    notification,
)
from ..settings.constants import settings
from ..api.client import Client

_logger = logging.getLogger(__name__)


class ProviderJTExpress(models.Model):
    _inherit = 'delivery.carrier'

    _jtexpress_password_salt = 'jadada369t3'

    delivery_type = fields.Selection(
        selection_add=[('jtexpress', 'J&T Express')],
        ondelete={'jtexpress': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})}
    )

    # ------------------------------------------------------------------
    # Default shipment parameter fields
    # ------------------------------------------------------------------
    default_jtexpress_payment_type = fields.Selection(
        selection=settings.payment_type.value,
        string='Payment Type',
        default=settings.default_payment_type.value
    )
    default_jtexpress_order_type = fields.Selection(
        selection=settings.order_type.value,
        string='Order Type',
        default=settings.default_order_type.value
    )
    default_jtexpress_service_type = fields.Selection(
        selection=settings.service_type.value,
        string='Service Type',
        default=settings.default_service_type.value
    )
    default_jtexpress_product_type = fields.Selection(
        selection=settings.product_type.value,
        string='Product Type',
        default=settings.default_product_type.value
    )
    default_jtexpress_goods_type = fields.Selection(
        selection=settings.goods_type.value,
        string='Goods Type',
        default=settings.default_goods_type.value
    )

    # ------------------------------------------------------------------
    # Environment toggle
    # ------------------------------------------------------------------
    def jtexpress_toggle_prod_environment(self):
        self.ensure_one()
        if self.prod_environment:
            self.domain = settings.domain_production.value
        else:
            self.domain = settings.domain_staging.value

    # ------------------------------------------------------------------
    # Credential verification
    # J&T Express uses per-request digest authentication – no bearer token.
    # ------------------------------------------------------------------
    def jtexpress_get_access_token(self):
        """Validate credentials and derive the J&T password from api_key."""
        self.ensure_one()
        missing = []
        if not self.client_id:
            missing.append('API Account (apiAccount)')
        elif not self.client_secret:
            missing.append('Private Key')
        elif not self.partner_id:
            missing.append('Customer Code (customerCode)')
        elif not self.api_key:
            missing.append('API Key')
        if missing:
            raise UserError(_('J&T Express: Thiếu thông tin cấu hình: %s') % ', '.join(missing))

        password_raw = f'{self.api_key}{self._jtexpress_password_salt}'
        password_hash = hashlib.md5(password_raw.encode('utf-8')).hexdigest().upper()
        self.write({'password': password_hash})

        return notification(
            'success',
            'J&T Express: Đã cập nhật Customer Password từ API Key bằng MD5(api_key + jadada369t3).'
        )

    # ------------------------------------------------------------------
    # Rate shipment (estimate cost via /api/spmComCost/getComCost)
    # ------------------------------------------------------------------
    def _get_default_rate_context(self, order):
        if self.delivery_type != settings.code.value:
            return super()._get_default_rate_context(order)
        return {
            'jtexpress_total_weight': order._get_estimated_weight() or 0,
            'jtexpress_service_type': self.default_jtexpress_service_type or settings.default_service_type.value,
            'jtexpress_payment_type': self.default_jtexpress_payment_type or settings.default_payment_type.value,
        }

    def _jtexpress_get_shipping_weight(self, order):
        return (
            self.env.context.get('order_weight')
            or self.env.context.get('jtexpress_total_weight')
            or order._get_estimated_weight()
            or 0
        )

    def _jtexpress_payload_estimate_cost(self, order):
        weight_kg = round(max(self.convert_weight(self._jtexpress_get_shipping_weight(order), 'KG'), 0.01), 2)
        warehouse = order.warehouse_id.partner_id
        recipient = order.partner_shipping_id
        if not warehouse:
            raise UserError(_('The address of warehouse is empty.'))
        elif not warehouse.state_id:
            raise UserError(_('The state of warehouse is empty.'))
        elif not warehouse.ward_id:
            raise UserError(_('The ward of warehouse is empty.'))
        elif not recipient.state_id:
            raise UserError(_('The recipient of warehouse is empty.'))
        elif not recipient.ward_id:
            raise UserError(_('The ward of recipient is empty.'))

        return {
            'customerCode': self.partner_id,
            'password': self.password,
            'weight': weight_kg,
            'isInsured': 0,
            'goodsValue': order.amount_total,
            'goodsType': order.env.context.get(
                'jtexpress_product_type',
                self.default_jtexpress_goods_type or settings.default_goods_type.value
            ),
            'codMoney': str(order.env.context.get('jtexpress_cod_amount', 0)),
            'productType': 'EXPRESS',
            'sender': {
                'prov': warehouse.state_id.name,
                'area': warehouse.ward_id.name
            },
            'receiver': {
                'prov': recipient.state_id.name,
                'area': recipient.ward_id.name
            },
        }

    def jtexpress_rate_shipment(self, order):
        try:
            client = Client(self)
            result = client.estimate_cost(self._jtexpress_payload_estimate_cost(order))
            freight = float(result.get('inquiryFee') or result.get('totalFee') or result.get('fee') or 0)
            return {
                'success': True,
                'price': freight,
                'error_message': False,
                'warning_message': False,
            }
        except Exception as e:
            return {
                'success': False,
                'price': 0.0,
                'error_message': str(e),
                'warning_message': False,
            }

    # ------------------------------------------------------------------
    # Create order (POST /api/order/addOrder)
    # ------------------------------------------------------------------
    def _jtexpress_payload_create_order(self, picking):
        sender_id = picking.picking_type_id.warehouse_id.partner_id
        recipient_id = picking.partner_id
        sale = picking.sale_id

        if not sender_id:
            raise UserError(_('Không tìm thấy địa chỉ người gửi (partner của kho hàng).'))
        sender_phone = sender_id.phone or getattr(sender_id, 'mobile', None) or ''
        if not sender_phone:
            raise UserError(_('Người gửi %s chưa có số điện thoại.') % sender_id.name)
        if not recipient_id:
            raise UserError(_('Phiếu giao hàng không có địa chỉ người nhận.'))
        receiver_phone = recipient_id.phone or getattr(recipient_id, 'mobile', None) or ''
        if not receiver_phone:
            raise UserError(_('Người nhận %s chưa có số điện thoại.') % recipient_id.name)

        weight_kg = round(max(
            self.convert_weight(picking._get_estimated_weight(), 'KG'),
            0.1
        ), 2)

        # Build item list from stock moves
        items = []
        for line in picking.move_ids:
            if line.product_id:
                items.append({
                    'itemName': line.product_id.name or 'Hàng hóa',
                    'englishName': line.product_id.name or 'Goods',
                    'number': str(int(line.product_qty or 1)),
                    'itemValue': int(line.product_id.lst_price or 0),
                })
        if not items:
            items = [{'itemName': 'Hàng hóa', 'englishName': 'Goods', 'number': '1', 'itemValue': 0}]

        payload = {
            'customerCode': self.partner_id,
            'password': self.password,
            'txlogisticId': sale.name if sale else picking.name,
            'orderType': int(self.default_jtexpress_order_type or '1'),
            'serviceType': int(self.default_jtexpress_service_type or '1'),
            'payType': self.default_jtexpress_payment_type or 'PP_CASH',
            'productType': self.default_jtexpress_product_type or 'EXPRESS',
            'goodsType': picking.jtexpress_goods_type or self.default_jtexpress_goods_type or 'bm000010',
            'deliveryType': 1,
            'isInsured': 0,
            'goodsValue': int(sale.amount_total if sale else 0),
            'sender': {
                'name': sender_id.name or '',
                'mobile': standardization_e164(sender_phone),
                'prov': sender_id.state_id.name if sender_id.state_id else '',
                'area': (sender_id.x_ward_id.name
                         if hasattr(sender_id, 'x_ward_id') and sender_id.x_ward_id
                         else ''),
                'address': sender_id.street or '',
            },
            'receiver': {
                'name': recipient_id.name or '',
                'mobile': standardization_e164(receiver_phone),
                'prov': recipient_id.state_id.name if recipient_id.state_id else '',
                'area': (recipient_id.x_ward_id.name
                         if hasattr(recipient_id, 'x_ward_id') and recipient_id.x_ward_id
                         else ''),
                'address': recipient_id.street or '',
            },
            'packageInfo': {
                'weight': str(weight_kg),
            },
            'items': items,
            'totalQuantity': len(items),
            'remark': getattr(picking, 'remarks', '') or '',
        }

        # COD (Cash on Delivery)
        if getattr(picking, 'cash_on_delivery', False) and getattr(picking, 'cash_on_delivery_amount', 0):
            payload['codMoney'] = str(int(picking.cash_on_delivery_amount))

        return payload

    @staticmethod
    def _jtexpress_payload_carrier_ref_order(picking):
        return {
            'jtexpress_goods_type': picking.jtexpress_goods_type,
        }

    def jtexpress_send_shipping(self, pickings):
        res = []
        for picking in pickings:
            ref_id = self.env['carrier.ref.order'].search([('picking_id', '=', picking.id)])
            if ref_id and ref_id.delivery_status_id.code not in settings.allow_booking_status.value:
                raise UserError(_('Phiếu giao hàng này đã được đặt. Vui lòng không đặt lại.'))

            client = Client(self)
            result = client.create_order(self._jtexpress_payload_create_order(picking))

            # Response: {"code":"1","data":{"billCode":"...","txlogisticId":"...","inquiryFee":...}}
            bill_code = result.get('billCode') or result.get('billcode') or ''
            freight = float(result.get('inquiryFee') or result.get('totalFee') or 0)

            status_id = self.env.ref(
                'tangerine_delivery_jtexpress.jtexpress_status_created',
                raise_if_not_found=False
            )
            picking.write({'delivery_status_id': status_id.id if status_id else False})

            self.env['carrier.ref.order'].create([{
                **self.common_payload_carrier_ref_order(picking, status_id, freight, bill_code),
                **self._jtexpress_payload_carrier_ref_order(picking),
            }])

            res.append({
                'exact_price': freight,
                'tracking_number': bill_code,
            })
        return res

    def _jtexpress_get_status_from_scan_type(self, scan_type_code):
        self.ensure_one()
        if scan_type_code is None:
            return self.env['delivery.status']
        status_code = settings.scan_type_code_to_status.value.get(int(scan_type_code))
        if not status_code:
            return self.env['delivery.status']
        return self.env['delivery.status'].search([
            ('code', '=', status_code),
            ('provider_id', '=', self.id),
        ], limit=1)

    def _jtexpress_update_order_status(self, ref_order, scan_type_code):
        self.ensure_one()
        status_id = self._jtexpress_get_status_from_scan_type(scan_type_code)
        if not status_id:
            return self.env['delivery.status']
        ref_order.sudo().write({'delivery_status_id': status_id.id})
        ref_order.picking_id.sudo().write({'delivery_status_id': status_id.id})
        return status_id

    @api.model
    def _cron_sync_jtexpress_status(self):
        carrier_ids = self.search([('delivery_type', '=', settings.code.value)])
        for carrier in carrier_ids:
            pending_orders = self.env['carrier.ref.order'].search([
                ('carrier_id', '=', carrier.id),
                ('delivery_status_id.code', 'not in', ['DELIVERED', 'RETURNED', 'CANCELLED']),
                ('carrier_tracking_ref', '!=', False),
            ])
            if not pending_orders:
                continue

            client = Client(carrier)
            for ref_order in pending_orders:
                try:
                    result = client.track_order({
                        'customerCode': carrier.partner_id,
                        'password': carrier.password,
                        'txlogisticId': '',
                        'billCodes': ref_order.carrier_tracking_ref,
                    })
                    details = result.get('details') or []
                    if details:
                        carrier._jtexpress_update_order_status(ref_order, details[0].get('scanTypeCode'))
                except Exception:
                    _logger.exception('J&T Express cron sync failed for tracking ref %s', ref_order.carrier_tracking_ref)

    # ------------------------------------------------------------------
    # Cancel order (POST /api/order/cancelOrder)
    # ------------------------------------------------------------------
    def _jtexpress_payload_cancel_order(self, picking):
        sale = picking.sale_id
        return {
            'customerCode': self.partner_id,
            'password': self.password,
            'txlogisticId': sale.name if sale else picking.name,
            'reason': 'Huỷ đơn hàng',
        }

    def jtexpress_cancel_shipment(self, pickings):
        self.ensure_one()
        client = Client(self)
        status_id = self.env.ref(
            'tangerine_delivery_jtexpress.jtexpress_status_cancelled',
            raise_if_not_found=False
        )
        tracked_pickings = pickings.filtered('carrier_tracking_ref')
        if not tracked_pickings and len(pickings) == 1:
            raise UserError(_('Không tìm thấy mã vận đơn để huỷ.'))

        for picking in tracked_pickings:
            ref_order = self.env['carrier.ref.order'].search([('picking_id', '=', picking.id)], limit=1)
            if ref_order and ref_order.delivery_status_id.code == 'CANCELLED':
                continue

            client.cancel_order(self._jtexpress_payload_cancel_order(picking))
            picking.write({
                'carrier_price': 0.0,
                'delivery_status_id': status_id.id if status_id else False,
            })
            if ref_order:
                ref_order.write({
                    'delivery_status_id': status_id.id if status_id else False,
                })

    # ------------------------------------------------------------------
    # Tracking link
    # ------------------------------------------------------------------
    @staticmethod
    def jtexpress_get_tracking_link(picking):
        return f'{settings.tracking_url.value}{picking.carrier_tracking_ref}'
