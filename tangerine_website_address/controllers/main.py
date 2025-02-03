from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleModesk(WebsiteSale):

    def _get_mandatory_fields_shipping(self, country_id=False):
        req = super(WebsiteSaleModesk, self)._get_mandatory_fields_shipping(country_id)
        req += ['district_id', 'ward_id']
        return req

    def _get_country_related_render_values(self, kw, render_values):
        res = super(WebsiteSaleModesk, self)._get_country_related_render_values(kw, render_values)
        """ Provide the fields related to the country to render the website sale form """
        values = render_values['checkout']
        mode = render_values['mode']
        order = render_values['website_sale_order']

        def_state_id = order.partner_id.state_id
        def_district_id = order.partner_id.district_id
        def_ward_id = order.partner_id.ward_id

        if res.get('country') and res.get('country').code == 'VN':
            state = 'state_id' in values and values['state_id'] != '' and request.env['res.country.state'].browse(int(values['state_id']))
            district = 'district_id' in values and values['district_id'] != '' and request.env['res.country.district'].browse(int(values['district_id']))
            ward = 'ward_id' in values and values['ward_id'] != '' and request.env['res.country.ward'].browse(int(values['ward_id']))

            state = state and state.exists() or def_state_id
            district = district and district.exists() or def_district_id
            ward = ward and ward.exists() or def_ward_id

            res.update({
                'state': state,
                'district': district,
                'state_districts': state.get_website_sale_districts(mode=mode[1]),
                'ward': ward,
                'district_wards': district.get_website_sale_wards(mode=mode[1]),
            })
        return res

    @http.route('/shop/district_infos/<model("res.country.state"):state>', type='json', auth='public', methods=['POST'], website=True)
    def district_infos(self, state, mode, **kw):
        return {
            'districts': [(d.id, d.name, d.code) for d in state.get_website_sale_districts(mode=mode)]
        }

    @http.route('/shop/ward_infos/<model("res.country.district"):district>', type='json', auth='public', methods=['POST'], website=True)
    def ward_infos(self, district, mode, **kw):
        return {
            'wards': [(w.id, w.name, w.code) for w in district.get_website_sale_wards(mode=mode)]
        }