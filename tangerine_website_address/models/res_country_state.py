from odoo import models


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    def get_website_sale_districts(self, mode='billing'):
        return self.sudo().district_ids