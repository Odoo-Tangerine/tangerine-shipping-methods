# -*- coding: utf-8 -*-
{
    'name': 'Shipping Methods Base',
    'summary': """This module handles Restful APIs between the Odoo system and third-party service carriers.""",
    'author': 'Long Duong Nhat',
    'website': 'https://github.com/long-dn',
    'license': 'LGPL-3',
    'category': 'Inventory/Delivery',
    'support': 'odoo.tangerine@gmail.com',
    'version': '1.0.0',
    'depends': ['mail', 'base', 'sale_stock', 'stock_delivery', 'purchase', 'tangerine_address_base'],
    'data': [
        'security/ir.model.access.csv',
        'security/carrier_ref_order_rules.xml',
        'data/cron.xml',
        'data/delivery_standard_status_data.xml',
        'data/res_partner_data.xml',
        'wizard/print_order_wizard_views.xml',
        'wizard/cod_reconciliation_import_wizard_views.xml',
        # 'wizard/compare_carrier_rates_wizard_views.xml',  # DISABLED
        'views/delivery_dashboard_views.xml',
        'views/delivery_base_views.xml',
        'views/delivery_route_api_views.xml',
        'views/delivery_status_views.xml',
        'views/delivery_standard_status_views.xml',
        'views/carrier_ref_order_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_warehouse_views.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'views/delivery_webhook_log_views.xml',
        'views/ir_cron_views.xml',
        'views/cod_reconciliation_views.xml',
        'views/menus.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'tangerine_delivery_base/static/src/css/delivery_dashboard.css',
            'tangerine_delivery_base/static/src/js/delivery_dashboard.js',
            'tangerine_delivery_base/static/src/xml/delivery_dashboard.xml',
        ],
    },
    'images': ['static/description/thumbnail.png'],
    'installable': True,
    'auto_install': False,
    'application': True
}
