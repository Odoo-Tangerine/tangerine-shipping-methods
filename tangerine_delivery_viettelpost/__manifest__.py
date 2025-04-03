# -*- coding: utf-8 -*-
{
    'name': 'Viettel Post Integration',
    'summary': """Viettel Post Integration module will allow shippers to easily place, cancel, get quotes, and track orders via simple integration for delivery in Odoo.""",
    'author': 'Long Duong Nhat',
    'category': 'Inventory/Delivery',
    'support': 'odoo.tangerine@gmail.com',
    'version': '18.0.1.0',
    'depends': ['tangerine_delivery_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/delivery_viettelpost_data.xml',
        'data/viettelpost_route_api_data.xml',
        'data/viettelpost_status_data.xml',
        'data/res_partner_data.xml',
        'data/ir_cron.xml',
        'wizard/choose_delivery_carrier_wizard_views.xml',
        'wizard/print_order_wizard_views.xml',
        'views/delivery_viettelpost_views.xml',
        'views/stock_picking_views.xml',
        'views/viettelpost_service_views.xml',
        'views/viettelpost_service_extend_views.xml',
        'views/carrier_ref_order_views.xml'
    ],
    'post_init_hook': '_generate_master_data',
    'images': ['static/description/thumbnail.png'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': True,
    'currency': 'USD',
    'price': 119.00
}