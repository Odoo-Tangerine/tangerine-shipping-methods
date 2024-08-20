# -*- coding: utf-8 -*-
from enum import Enum


class settings(Enum):
    domain = 'https://partner-api.grab.com'
    grab_code = 'grab'
    staging_route = 'grab-express-sandbox'
    production_route = 'grab-express'

    tracking_url = 'https://partner-api.grab.com/tracking'
    oauth_route_code = 'oauth_route'
    get_quotes_route_code = 'get_delivery_quotes'
    create_request_route_code = 'create_delivery_request'
    cancel_request_route_code = 'cancel_delivery'

    service_type = [
        ('INSTANT', 'Instant'),
        ('SAME_DAY', 'Same Day'),
        ('BULK', 'Bulk')
    ]
    default_service_type = 'INSTANT'

    vehicle_type = [
        ('BIKE', 'Bike'),
        ('CAR', 'Car'),
        ('JUSTEXPRESS', 'Just Express'),
        ('VAN', 'VAN'),
        ('TRUCK', 'Truck'),
        ('TRIKE', 'Trike'),
        ('EBIKE', 'EBike'),
        ('SUV', 'SUV'),
        ('BOXPICKUPTRUCK', 'Box Pickup Truck'),
        ('TRICYCLE', 'Tricycle'),
        ('CYCLE', 'Cycle'),
        ('FOOT', 'Foot'),
    ]
    default_vehicle_type = 'BIKE'

    payment_method = [
        ('CASHLESS', 'Cashless'),
        ('CASH', 'Cash')
    ]
    default_payment_method = 'CASHLESS'

    payer = [
        ('SENDER', 'Sender'),
        ('RECIPIENT', 'Recipient')
    ]
    default_payer = 'SENDER'

    cod_type = [
        ('REGULAR', 'Regular'),
        ('ADVANCED', 'Advanced')
    ]

    default_cod_type = 'REGULAR'

    list_status_cancellation_allowed = ['IN_DELIVERY', 'FAILED', 'CANCELED', 'COMPLETED']
    allow_booking_status = ['COMPLETED', 'FAILED', 'CANCELED', 'RETURNED']
    block_webhook_change_status = ['COMPLETED', 'FAILED', 'CANCELED', 'RETURNED']
    status_completed = 'COMPLETED'

