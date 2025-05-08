from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleModesk(WebsiteSale):

    def _get_mandatory_address_fields(self, country_sudo):
        req = super(WebsiteSaleModesk, self)._get_mandatory_address_fields(country_sudo)
        if country_sudo.code == 'VN':
            req.add('district_id')
            req.add('ward_id')
        return req

    def _prepare_address_form_values(
            self, order_sudo, partner_sudo, address_type, use_delivery_as_billing, callback='', **kwargs
    ):
        res = super(WebsiteSaleModesk, self)._prepare_address_form_values(
            order_sudo, partner_sudo, address_type, use_delivery_as_billing, callback, **kwargs
        )
        if partner_sudo.country_id.code == 'VN':
            res.update({
                'district_id': partner_sudo.district_id.id,
                'state_districts': partner_sudo.state_id.district_ids,
                'ward_id': partner_sudo.ward_id.id,
                'district_wards': partner_sudo.district_id.ward_ids,
            })
        return res

    @http.route('/shop/district_info/<model("res.country.state"):state>', type='json', auth='public', methods=['POST'], website=True)
    def district_infos(self, state, **kw):
        return {
            'districts': [(d.id, d.name, d.code) for d in state.sudo().district_ids]
        }

    @http.route('/shop/ward_info/<model("res.country.district"):district>', type='json', auth='public', methods=['POST'], website=True)
    def ward_infos(self, district, **kw):
        return {
            'wards': [(w.id, w.name, w.code) for w in district.sudo().ward_ids]
        }