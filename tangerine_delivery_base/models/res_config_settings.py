from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    webhook_log_retention_days = fields.Integer(string='Webhook Log Retention (days)', default=30, config_parameter='tangerine_delivery_base.webhook_log_retention_days', help='Automatically delete webhook logs older than this number of days. Set 0 to disable auto-delete.')

    @api.model
    def get_values(self):
        OOOOOO0OOO00O0OOO = super().get_values()
        OO0O0OO000OOO0O0O = self.env['ir.config_parameter'].sudo()
        OOOOOO0OOO00O0OOO['webhook_log_retention_days'] = int(OO0O0OO000OOO0O0O.get_param('tangerine_delivery_base.webhook_log_retention_days', default='30'))
        return OOOOOO0OOO00O0OOO

    def set_values(self):
        super().set_values()
        OOO0OO0OO00OOO0OO = self.env['ir.config_parameter'].sudo()
        OOO0OO0OO00OOO0OO.set_param('tangerine_delivery_base.webhook_log_retention_days', str(self.webhook_log_retention_days))