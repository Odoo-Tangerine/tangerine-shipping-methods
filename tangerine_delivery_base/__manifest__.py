# -*- coding: utf-8 -*-
{
    'name': 'Shipping Methods Base',
    'summary': """This module handles Restful APIs between the Odoo system and third-party service carriers.""",
    'author': 'Long Duong Nhat',
    'license': 'LGPL-3',
    'category': 'Inventory/Delivery',
    'support': 'odoo.tangerine@gmail.com',
    'version': '17.0.1.0',
    'depends': ['mail', 'base', 'delivery', 'sale', 'stock', 'sale_stock', 'tangerine_address_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/res_partner_data.xml',
        'wizard/print_order_wizard_views.xml',
        'views/delivery_base_views.xml',
        'views/delivery_route_api_views.xml',
        'views/delivery_status_views.xml',
        'views/carrier_ref_order_views.xml',
        'views/stock_picking_views.xml',
        'views/menus.xml'
    ],
    'images': ['static/description/thumbnail.png'],
    'installable': True,
    'auto_install': False,
    'application': False
}