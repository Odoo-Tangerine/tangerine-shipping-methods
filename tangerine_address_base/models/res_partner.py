# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    ward_id = fields.Many2one(
        comodel_name='res.country.ward',
        string='Ward',
        domain="[('state_id', '=?', state_id)]"
    )


    shipping_address = fields.Char(compute='_compute_complete_shipping_address')
    vn_address_complete = fields.Char(compute='_compute_address_structure')

    @api.depends('country_id', 'state_id', 'ward_id', 'street')
    def _compute_address_structure(self):
        for rec in self:
            rec.vn_address_complete = False
            if rec.country_id.code == 'VN':
                rec.vn_address_complete = f'{rec.street or ""}, {rec.ward_id.display_name or ""}, {rec.state_id.display_name or ""}, {rec.country_id.name or ""}'.strip(', ')
