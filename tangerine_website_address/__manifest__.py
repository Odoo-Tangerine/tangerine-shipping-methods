# -*- coding: utf-8 -*-
{
    'name': 'Vietnam Wards on Website',
    'summary': """The Vietnam Wards on Website Module enhances address selection by dynamically filtering districts and wards based on the selected country and state/province on website""",
    'author': 'Long Duong Nhat',
    'license': 'LGPL-3',
    'category': 'Extra Tools',
    'version': '1.0.0',
    'support': 'odoo.tangerine@gmail.com',
    'depends': ['web', 'portal', 'website_sale', 'tangerine_address_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_model_data.xml',
        'views/portal_templates.xml',
    ],
    'images': ['static/description/thumbnail.png'],
    'assets': {
        'web.assets_frontend': [
            'tangerine_website_address/static/src/interactions/**/*',
        ],
    },
    'application': False,
    'installable': True,
}
