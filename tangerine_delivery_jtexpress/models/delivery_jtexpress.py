# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError

from odoo.addons.tangerine_delivery_base.settings.utils import (
    standardization_e164,
    notification,
)
from ..settings.constants import settings
from ..api.client import Client


class ProviderJTExpress(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('jtexpress', 'J&T Express')],
        ondelete={'jtexpress': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})}
    )

    # ------------------------------------------------------------------
    # J&T Express credential fields
    # ------------------------------------------------------------------
    jtexpress_api_account = fields.Char(
        string='API Account',
        help='apiAccount – Mã tài khoản API trên cổng J&T Express Open Platform. '
             'Dùng trong HTTP header của mỗi request.'
    )
    # api_key (inherited from delivery.carrier base) is reused as privateKey
    # for computing: digest = base64(md5(bizContent + privateKey))

    jtexpress_customer_code = fields.Char(
        string='Customer Code',
        help='customerCode – Mã khách hàng do điểm đại lý J&T Express cung cấp. '
             'Dùng trong trường bizContent.'
    )
    jtexpress_password = fields.Char(
        string='Customer Password',
        help='password – Mật khẩu tài khoản mở nền. Dùng trong trường bizContent.'
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
        """Validate that all required J&T Express credentials are configured."""
        self.ensure_one()
        missing = []
        if not self.jtexpress_api_account:
            missing.append('API Account (apiAccount)')
        if not self.api_key:
            missing.append('Private Key')
        if not self.jtexpress_customer_code:
            missing.append('Customer Code (customerCode)')
        if not self.jtexpress_password:
            missing.append('Customer Password')
        if missing:
            raise UserError(
                _('J&T Express: Thiếu thông tin cấu hình: %s') % ', '.join(missing)
            )
        return notification(
            'success',
            'J&T Express: Thông tin xác thực đã được cấu hình đầy đủ. '
            'Xác thực mỗi request bằng digest = base64(md5(bizContent + privateKey)).'
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

    def _jtexpress_payload_estimate_cost(self, order):
        weight_kg = round(max(
            self.convert_weight(order._get_estimated_weight(), 'KG'),
            0.01
        ), 2)
        warehouse_partner = order.warehouse_id.partner_id if order.warehouse_id else None
        recipient = order.partner_shipping_id
        return {
            'customerCode': self.jtexpress_customer_code,
            'weight': str(weight_kg),
            'sender': {
                'prov': warehouse_partner.state_id.name if warehouse_partner and warehouse_partner.state_id else '',
                'city': (warehouse_partner.x_city_id.name
                         if warehouse_partner and hasattr(warehouse_partner, 'x_city_id') and warehouse_partner.x_city_id
                         else ''),
                'area': (warehouse_partner.x_ward_id.name
                         if warehouse_partner and hasattr(warehouse_partner, 'x_ward_id') and warehouse_partner.x_ward_id
                         else ''),
            },
            'receiver': {
                'prov': recipient.state_id.name if recipient and recipient.state_id else '',
                'city': (recipient.x_city_id.name
                         if recipient and hasattr(recipient, 'x_city_id') and recipient.x_city_id
                         else ''),
                'area': (recipient.x_ward_id.name
                         if recipient and hasattr(recipient, 'x_ward_id') and recipient.x_ward_id
                         else ''),
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
            'customerCode': self.jtexpress_customer_code,
            'password': self.jtexpress_password,
            'txlogisticId': sale.name if sale else picking.name,
            'orderType': int(picking.jtexpress_order_type or self.default_jtexpress_order_type or '1'),
            'serviceType': int(picking.jtexpress_service_type or self.default_jtexpress_service_type or '1'),
            'payType': picking.jtexpress_payment_type or self.default_jtexpress_payment_type or 'PP_CASH',
            'productType': self.default_jtexpress_product_type or 'EXPRESS',
            'goodsType': self.default_jtexpress_goods_type or 'bm000010',
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
            'jtexpress_payment_type': picking.jtexpress_payment_type,
            'jtexpress_order_type': picking.jtexpress_order_type,
            'jtexpress_service_type': picking.jtexpress_service_type,
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

    # ------------------------------------------------------------------
    # Cancel order (POST /api/order/cancelOrder)
    # ------------------------------------------------------------------
    def _jtexpress_payload_cancel_order(self, picking):
        sale = picking.sale_id
        return {
            'customerCode': self.jtexpress_customer_code,
            'password': self.jtexpress_password,
            'txlogisticId': sale.name if sale else picking.name,
            'reason': 'Huỷ đơn hàng',
        }

    def jtexpress_cancel_shipment(self, picking):
        if not picking.carrier_tracking_ref:
            raise UserError(_('Không tìm thấy mã vận đơn để huỷ.'))

        client = Client(self)
        client.cancel_order(self._jtexpress_payload_cancel_order(picking))

        status_id = self.env.ref(
            'tangerine_delivery_jtexpress.jtexpress_status_cancelled',
            raise_if_not_found=False
        )
        picking.write({
            'carrier_tracking_ref': False,
            'carrier_price': 0.0,
            'delivery_status_id': status_id.id if status_id else False,
        })
        return notification('success', 'Đã huỷ đơn hàng J&T Express thành công.')

    # ------------------------------------------------------------------
    # Tracking link
    # ------------------------------------------------------------------
    @staticmethod
    def jtexpress_get_tracking_link(picking):
        return f'{settings.tracking_url.value}{picking.carrier_tracking_ref}'
