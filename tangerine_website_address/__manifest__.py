# -*- coding: utf-8 -*-
{
    'name': 'Vietnam Districts/Wards On Website',
    'summary': """The Vietnam Districts/Wards On Website Module enhances address selection by dynamically filtering districts and wards based on the selected country and state/province on website""",
    'author': 'Long Duong Nhat',
    'license': 'LGPL-3',
    'category': 'Extra Tools',
    'version': '17.0.1.0',
    'support': 'odoo.tangerine@gmail.com',
    'depends': ['web', 'portal', 'website', 'tangerine_address_base'],
    'data': [
        'data/ir_model_data.xml',
        'views/templates.xml',
        'views/portal_templates.xml',
    ],
    'images': ['static/description/thumbnail.png'],
    'assets': {
        'web.assets_frontend': [
            'tangerine_website_address/static/src/js/website_sale.js',
            'tangerine_website_address/static/src/js/portal.js',
        ],
    },
    'application': False,
    'installable': True,
    'currency': 'USD',
    'price': 25.00
}
