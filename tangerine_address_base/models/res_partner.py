# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    # outdated
    district_id = fields.Many2one(
        comodel_name='res.country.district',
        string='District',
        domain="[('state_id','=', state_id)]"
    )
    ward_id = fields.Many2one(
        comodel_name='res.country.ward',
        string='Ward/Commune',
        domain="[('state_id', '=', state_id)]"
    )
    full_address = fields.Char(compute='_compute_address_structure')

    @api.depends('country_id', 'state_id', 'ward_id', 'street')
    def _compute_address_structure(self):
        self.full_address = False
        for rec in self:
            if rec.country_id and rec.country_id.code == 'VN':
                address_parts = [
                    rec.street,
                    rec.ward_id.display_name,
                    rec.state_id.display_name,
                    rec.country_id.display_name
                ]
                rec.full_address = ', '.join(filter(None, address_parts))
