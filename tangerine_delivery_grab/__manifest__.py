# -*- coding: utf-8 -*-
{
    'name': 'Grab Express Integration',
    'summary': """Grab Express Integration will allow Odooers to easily place, cancel, get quotes, and track the order via simple integration.""",
    'author': 'Long Duong Nhat',
    'category': 'Inventory/Delivery',
    'support': 'odoo.tangerine@gmail.com',
    'version': '17.0.1.0',
    'depends': ['tangerine_delivery_base'],
    'data': [
        'data/delivery_grab_data.xml',
        'data/grab_route_api_data.xml',
        'data/grab_status_data.xml',
        'data/ir_cron.xml',
        'data/res_partner_data.xml',
        'data/res_country_state_data.xml',
        'wizard/choose_delivery_carrier_wizard_views.xml',
        'views/delivery_grab_views.xml',
        'views/stock_picking_views.xml',
        'views/carrier_ref_order_views.xml',
    ],
    'images': ['static/description/thumbnail.png'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': True,
    'currency': 'USD',
    'price': 119.00
}