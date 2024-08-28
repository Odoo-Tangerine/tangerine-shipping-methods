# -*- coding: utf-8 -*-
from enum import Enum
from typing import Final


class settings(Enum):
    domain_production = 'https://api.247express.vn'
    domain_staging = 'https://customerapi-dev.247tech.xyz'
    tracking_domain_production = 'https://tracking.247express.vn'
    tracking_domain_staging = 'https://tracking-dev.247tech.xyz'
    code = 'express_247'

    get_access_token_route_code = 'express_247_get_access_token'
    get_service_type_route_code = 'express_247_get_service_type'
    get_special_service_type_route_code = 'express_247_get_special_service_type'
    get_hubs_route_code = 'express_247_get_hubs'
    create_hub_route_code = 'express_247_create_hub'
    update_hub_route_code = 'express_247_update_hub'
    get_price_route_code = 'express_247_get_price'
    create_order_route_code = 'express_247_create_order'
    cancel_order_code = 'express_247_cancel_order'
    print_order_route_code = 'express_247_print_order'
    tracking_order_route_code = 'express_247_tracking_order'

    default_service_type = 'DE'

    product_type = [
        ('HH', 'Goods'),
        ('TL', 'Document')
    ]

    default_product_type = 'HH'
