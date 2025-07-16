# -*- coding: utf-8 -*-
from enum import Enum
from typing import Final


class settings(Enum):
    domain_staging = 'https://apistg.ahamove.com'
    domain_production = 'https://api.ahamove.com'
    tracking_url_staging = 'https://cloudstg.ahamove.com'
    tracking_url_production = 'https://cloud.ahamove.com'
    ahamove_code = 'ahamove'

    get_token_route_code = 'get_token'
    estimate_order_route_code = 'estimate_order'
    create_order_route_code = 'create_order'
    cancel_order_route_code = 'cancel_order'
    city_sync_route_code = 'city_sync'
    service_sync_route_code = 'service_sync'

    payment_method = [
        ('BALANCE', 'BALANCE'),
        ('CASH', 'CASH'),
    ]
    default_payment_method = 'BALANCE'

    request_group_bulky = 'BULKY'
    request_group_tip = 'TIP'
    default_tier = 'TIER_1'
    status_completed = 'COMPLETED'
    cancel_reason = 'Merchant asks for order cancellation'
    cancel_reason_code = 'partner_merchant_asks_for_order_cancellation'
    allow_booking_status = ['COMPLETED', 'CANCELLED']
    block_webhook_change_status = ['COMPLETED', 'CANCELLED', 'RETURNED']
