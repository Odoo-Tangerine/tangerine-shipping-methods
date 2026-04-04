# -*- coding: utf-8 -*-
from enum import Enum


class settings(Enum):
    # Carrier code
    code = 'jtexpress'

    # Domains (include base path /webopenplatformapi)
    domain_production = 'https://ylopenapi.jtexpress.vn/webopenplatformapi'
    domain_staging = 'https://demoopenapi.jtexpress.vn/webopenplatformapi'

    # Tracking URL
    tracking_url = 'https://jtexpress.vn/vi/tracking?type=track&billCode='

    # Route codes
    create_order_route = 'jtexpress_create_order'
    cancel_order_route = 'jtexpress_cancel_order'
    track_order_route = 'jtexpress_track_order'
    estimate_cost_route = 'jtexpress_estimate_cost'
    print_label_route = 'jtexpress_print_label'

    # payType field values
    payment_type = [
        ('PP_PM', 'Gửi trả - thanh toán tháng (PP_PM)'),
        ('PP_CASH', 'Gửi trả - thanh toán ngay (PP_CASH)'),
        ('CC_CASH', 'Người nhận trả - thanh toán ngay (CC_CASH)'),
    ]
    default_payment_type = 'PP_CASH'

    # orderType field values: 1 = normal, 2 = return
    order_type = [
        ('1', 'Đơn thường'),
        ('2', 'Đơn hoàn hàng'),
    ]
    default_order_type = '1'

    # serviceType field values: 1 = home pickup, 6 = drop at store
    service_type = [
        ('1', 'Giao tận nơi'),
        ('6', 'Gửi tại điểm (bưu cục)'),
    ]
    default_service_type = '1'

    # productType field values
    product_type = [
        ('EXPRESS', 'Express'),
        ('FAST', 'Fast'),
        ('SUPER', 'Super'),
    ]
    default_product_type = 'EXPRESS'

    # goodsType field values
    goods_type = [
        ('bm000001', 'Document'),
        ('bm000010', 'Goods'),
        ('bm000011', 'Fresh'),
    ]
    default_goods_type = 'bm000010'

    # Statuses that allow creating a new shipment order
    allow_booking_status = ['CREATED', 'CANCELLED']

    # Mapping from J&T scanTypeCode (int) → our delivery.status code (str)
    # scanTypeCode is sent by J&T webhook and track-order API
    scan_type_code_to_status = {
        103: 'CREATED',                          # Order Placed (J&T confirmed)
        104: 'EXCEPTION',                        # Pickup Failure
        105: 'CANCELLED',                        # Cancel Order
        106: 'PICKED_UP',                        # Picked Up (快件揽收)
        109: 'DEPARTURE_FROM_SORTING_CENTER',    # Departure scan (发件扫描)
        110: 'ARRIVED_AT_SORTING_CENTER',        # Arrival scan (到件扫描)
        112: 'IN_DELIVERY',                      # On Delivery (出仓扫描)
        113: 'DELIVERED',                        # Delivered (快件签收)
        116: 'RETURNING',                        # Returning (退件确认)
        117: 'RETURNED',                         # Returned Sign (退件签收)
        118: 'DELIVERY_FAILED',                  # Delivery Problem (派件问题件)
        120: 'EXCEPTION',                        # Return Problem (退件问题件)
        121: 'DELIVERED',                        # FINISH (完结)
    }
