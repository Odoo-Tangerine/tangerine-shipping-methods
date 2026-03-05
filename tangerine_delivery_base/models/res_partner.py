from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'
    type = fields.Selection(selection_add=[('post_office', 'Post Office'), ('other',)], ondelete={'post_office': 'set default'})
    shipping_address = fields.Char(compute='_compute_shipping_address')

    @api.depends('country_id', 'state_id', 'ward_id', 'street')
    def _compute_shipping_address(self):
        self.shipping_address = False
        for OOOOOO0OOO00O0OOO in self:
            if OOOOOO0OOO00O0OOO.country_id and OOOOOO0OOO00O0OOO.country_id.code == 'VN':
                OO0O0OO000OOO0O0O = [OOOOOO0OOO00O0OOO.street, OOOOOO0OOO00O0OOO.ward_id.name, OOOOOO0OOO00O0OOO.state_id.name, OOOOOO0OOO00O0OOO.country_id.name]
                OOOOOO0OOO00O0OOO.shipping_address = ', '.join(filter(None, OO0O0OO000OOO0O0O))