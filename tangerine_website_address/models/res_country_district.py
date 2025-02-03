from odoo import models


class ResCountryDistrict(models.Model):
    _inherit = 'res.country.district'

    def get_website_sale_wards(self, mode='billing'):
        return self.sudo().ward_ids