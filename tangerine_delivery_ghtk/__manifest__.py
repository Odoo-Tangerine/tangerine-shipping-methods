# -*- coding: utf-8 -*-
{
    'name': 'Giao Hang Tiet Kiem Integration',
    'summary': """Delivering the perfect solution for all your shipping needs with groundbreaking technology — all in a single app Giao Hang Tiet Kiem Integration.""",
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
    ],
    'images': ['static/description/thumbnail.png'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': True,
    'currency': 'USD',
    'price': 119.00
}