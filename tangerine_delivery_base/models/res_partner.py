from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    type = fields.Selection(
        selection_add=[
            ('post_office', 'Post Office'),
            ('other',)
        ],
        ondelete={'post_office': 'set default'}
    )
    
    shipping_address = fields.Char(compute='_compute_shipping_address')

    @api.depends('country_id', 'state_id', 'ward_id', 'street')
    def _compute_shipping_address(self):
        self.shipping_address = False
        for rec in self:
            if rec.country_id and rec.country_id.code == 'VN':
                address_parts = [
                    rec.street,
                    rec.ward_id.name,
                    rec.state_id.name,
                    rec.country_id.name
                ]
                rec.shipping_address = ', '.join(filter(None, address_parts))
