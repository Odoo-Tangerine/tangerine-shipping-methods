from odoo import fields, models


class AhamoveResState(models.Model):
    _inherit = 'res.country.state'

    ahamove_city_code = fields.Char(string='Ahamove Code')
