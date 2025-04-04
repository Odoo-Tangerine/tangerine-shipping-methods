from odoo import fields, models


class State(models.Model):
    _inherit = 'res.country.state'

    grab_city_code = fields.Char(string='Grab City Code')
