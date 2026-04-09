from odoo import fields, models


class IrCron(models.Model):
    _inherit = 'ir.cron'

    is_cron_delivery = fields.Boolean(string='Delivery Cron', default=False)
