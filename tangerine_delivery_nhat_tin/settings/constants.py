# -*- coding: utf-8 -*-
from enum import Enum


class settings(Enum):
    domain_staging = 'https://apisandbox.ntlogistics.vn'
    domain_production = 'https://apiws.ntlogistics.vn'
    domain_printer_staging = 'https://printdev.ntlogistics.vn'
    domain_printer_production = 'https://printdigi.ntlogistics.vn'
    nhat_tin_code = 'nhat_tin'

    ntl_create_bill_route_code = 'ntl_create_bill'
    ntl_calculate_price_route_code = 'ntl_calculate_price'
    ntl_cancel_bill_route_code = 'ntl_cancel_bill'
    ntl_print_bill_route_code = 'ntl_print_bill'
    ntl_connect_platform_route_code = 'ntl_connect_platform'

    service_type = [
        ('90', 'Express Delivery'),
        ('81', 'Premium Service'),
        ('91', 'Economic'),
        ('21', 'Mixed Express')
    ]

    default_service_type = '90'

    cargo_type = [
        ('1', 'Documents'),
        ('2', 'Goods'),
        ('3', 'Cold goods'),
        ('4', 'Biological products'),
        ('5', 'Specimens')
    ]

    default_cargo_type = '2'

    payment_method = [
        ('10', 'Sender pay by Cash when pick up / walk-in payment'),
        ('11', 'Payment by Sender according to contract'),
        ('20', 'Receiver pay by Cash when delivery'),
    ]

    default_payment_method = '10'
