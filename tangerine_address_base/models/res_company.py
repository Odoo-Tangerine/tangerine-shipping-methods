from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    ward_id = fields.Many2one(
        'res.country.ward',
        string='Ward',
        compute='_compute_address',
        inverse='_inverse_ward',
        domain="[('state_id', '=?', state_id)]"
    )

    def _get_company_address_field_names(self):
        res = super()._get_company_address_field_names()
        res.append('ward_id')
        return res

    def _inverse_ward(self):
        for company in self:
            company.partner_id.ward_id = company.ward_id
