from odoo import fields, models


class GHTKSpecialService(models.Model):
    _name = 'ghtk.special.service'
    _description = 'GHTK Special Service'

    provider_id = fields.Many2one('delivery.carrier', string='Carrier', ondelete='cascade')
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
