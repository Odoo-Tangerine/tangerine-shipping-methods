# -*- coding: utf-8 -*-
{
    'name': 'Giao Hang Tiet Kiem Integration',
    'summary': """The GHTK Integration for Odoo is designed to connect the Odoo ERP system seamlessly with Giao Hang Tiet Kiem. This module provides features like placing orders, getting quotes, printing shipping labels, etc.""",
    'author': 'Long Duong Nhat',
    'category': 'Inventory/Delivery',
    'support': 'odoo.tangerine@gmail.com',
    'version': '17.0.1.0',
    'depends': ['tangerine_delivery_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/delivery_ghtk_data.xml',
        'data/ghtk_route_api_data.xml',
        'data/ghtk_status_data.xml',
        'data/ghtk_special_service_data.xml',
        'data/res_partner_data.xml',
        'wizard/choose_delivery_carrier_wizard_views.xml',
        'wizard/print_order_wizard_views.xml',
        'views/delivery_ghtk_views.xml',
        'views/stock_picking_views.xml',
        'views/carrier_ref_order_views.xml'
    ],
    'images': ['static/description/thumbnail.png'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': True,
    'currency': 'USD',
    'price': 119.00
}