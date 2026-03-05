# -*- coding: utf-8 -*-
{
    'name': 'Vietnam Address',
    'summary': """The Vietnam Address Base module is an extension for the Odoo system designed to provide a comprehensive database of addresses in Vietnam.""",
    'author': 'Long Duong Nhat',
    'license': 'LGPL-3',
    'category': 'Extra Tools',
    'version': '1.0.0',
    'support': 'odoo.tangerine@gmail.com',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'data/res_country_state_data.xml',
        'data/res_country_ward_data.xml',
        'views/res_country_district_views.xml',
        'views/res_country_ward_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/menus.xml'
    ],
    'images': ['static/description/thumbnail.png'],
    'application': False,
    'installable': True,
}
