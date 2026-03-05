from odoo.http import route
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalModesk(CustomerPortal):

    def _get_mandatory_address_fields(self, country_sudo):
        required_fields = super()._get_mandatory_address_fields(country_sudo)
        if country_sudo.code == 'VN':
            required_fields.add('state_id')
            required_fields.add('ward_id')
        return required_fields

    def _prepare_address_form_values(self, partner_sudo, *args, **kwargs):
        rendering_values = super()._prepare_address_form_values(partner_sudo, *args, **kwargs)
        partner_sudo = rendering_values.get('partner_sudo')
        if not partner_sudo:
            partner_sudo = rendering_values.get('current_partner').sudo()
        if partner_sudo.country_id.code == 'VN':
            rendering_values.update({
                'ward_id': partner_sudo.ward_id.id,
                'state_wards': partner_sudo.state_id.ward_ids,
            })
        return rendering_values

    @route(
        route='/my/address/state_vn_info/<model("res.country.state"):state>',
        type='jsonrpc',
        auth='public',
        methods=['POST'],
        website=True,
        readonly=True
    )
    def state_infos(self, state, **kw):
        return {
            'wards': [(w.id, w.name, w.code) for w in state.sudo().ward_ids]
        }