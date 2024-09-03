from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    shipping_address_international = fields.Char(compute='_compute_shipping_address_international', store=True)

    @api.depends('street', 'zip', 'city', 'country_id')
    def _compute_shipping_address_international(self):
        for record in self:
            record.shipping_address_international = ''
            if record.street:
                record.shipping_address_international += record.street + ', '
            if record.zip:
                record.shipping_address_international += record.zip + ' '
            if record.city:
                record.shipping_address_international += record.city + ', '
            if record.state_id:
                record.shipping_address_international += record.state_id.name + ', '
            if record.country_id:
                record.shipping_address_international += record.country_id.name
            record.shipping_address_international = record.shipping_address_international.strip().strip(',')