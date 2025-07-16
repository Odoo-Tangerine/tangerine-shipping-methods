# -*- coding: utf-8 -*-
{
    'name': 'Nhat Tin Logistics Integration',
    'summary': """Nhat Tin Logistics Integration will allow Odooers to easily place, cancel, get quotes, and track the order via simple integration.""",
    'author': 'Long Duong Nhat',
    'category': 'Inventory/Delivery',
    'support': 'odoo.tangerine@gmail.com',
    'version': '18.0.1.0',
    'depends': ['tangerine_delivery_base'],
    'data': [
        'data/delivery_nhat_tin_data.xml',
        'data/nhat_tin_route_api_data.xml',
        'data/nhat_tin_status_data.xml',
        'data/res_partner_data.xml',
        'wizard/choose_delivery_carrier_wizard_views.xml',
        'views/delivery_nhat_tin_views.xml',
        'views/stock_picking_views.xml',
        'views/carrier_ref_order_views.xml',
    ],
    'images': ['static/description/thumbnail.gif'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': True,
    'currency': 'USD',
    'price': 119.00
}