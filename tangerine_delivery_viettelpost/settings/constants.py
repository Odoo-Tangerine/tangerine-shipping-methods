# -*- coding: utf-8 -*-
from enum import Enum
from typing import Final


class settings(Enum):
    domain_production = 'https://partner.viettelpost.vn'
    domain_staging = 'https://partnerdev.viettelpost.vn'
    tracking_url = 'https://viettelpost.vn/thong-tin-don-hang?peopleTracking=sender&orderNumber='
    code = 'viettelpost'

    get_short_term_token_route = 'viettelpost_get_short_term_token'
    get_long_term_token_route = 'viettelpost_get_long_term_token'
    service_sync_route = 'viettelpost_service_sync'
    service_extend_sync_route = 'viettelpost_service_extend_sync'
    get_matching_service_route = 'viettelpost_get_matching_service'
    estimate_cost_route = 'viettelpost_estimate_cost'
    create_order_route = 'viettelpost_create_order'
    update_order_route = 'viettelpost_update_order'
    viettelpost_print_order_route = 'viettelpost_print_order'

    url_print_a5 = 'https://digitalize.viettelpost.vn/DigitalizePrint/report.do?type=1&bill={}&showPostage=1'
    url_print_a6 = 'https://digitalize.viettelpost.vn/DigitalizePrint/report.do?type=2&bill={}&showPostage=1'
    url_print_a7 = 'https://digitalize.viettelpost.vn/DigitalizePrint/report.do?type=1001&bill={}&showPostage=1'

    product_type = [
        ('TH', 'Letter'),
        ('HH', 'Goods')
    ]
    default_product_type = 'HH'

    national_type = [
        ('0', 'International'),
        ('1', 'Domestic')
    ]
    default_national_type = '1'

    order_payment = [
        ('1', 'No collection'),
        ('2', 'Collect money for goods and delivery'),
        ('3', 'Collect money for goods'),
        ('4', 'Collect money for delivery')
    ]
    default_order_payment = '1'
    order_payment_no_collection = '1'
    order_payment_collect_money_for_goods_and_delivery = '2'
    order_payment_collect_money_for_goods = '3'
    order_payment_collect_money_for_delivery = '4'
    paper_size = [
        ('a5', 'A5 Paper'),
        ('a6', 'A6 Paper'),
        ('a7', 'A7 Paper')
    ]
    default_paper_print = 'a5'
    default_service_type = 'VCN'

    list_status_cancellation_allowed = ['IN_DELIVERY', 'FAILED', 'CANCELED', 'COMPLETED']
    status_completed = 'COMPLETED'
