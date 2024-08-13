# -*- coding: utf-8 -*-
from enum import Enum


class settings(Enum):
    domain_staging = 'https://rest.sandbox.lalamove.com'
    domain_production = 'https://rest.lalamove.com'
    lalamove_code = 'lalamove'

    llm_get_quotation_code = 'llm_get_quotation'
    llm_place_order_code = 'llm_place_order'
    llm_cancel_order_code = 'llm_cancel_order'
    llm_get_cities_code = 'llm_get_cities'
    llm_register_webhook = 'llm_register_webhook'

    weight_lt_10 = 'LESS_THAN_10_KG'
    weight_bw_10_30 = '10_KG_TO_30_KG'
    weight_bw_30_50 = '30_KG_TO_50_KG'

    webhook_order_status_changed = 'ORDER_STATUS_CHANGED'
    webhook_driver_assigned = 'DRIVER_ASSIGNED'
    webhook_order_amount_changed = 'ORDER_AMOUNT_CHANGED'
