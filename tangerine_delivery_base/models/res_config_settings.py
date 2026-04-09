from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    webhook_log_retention_days = fields.Integer(
        string='Webhook Log Retention (days)',
        default=30,
        config_parameter='tangerine_delivery_base.webhook_log_retention_days',
        help='Automatically delete webhook logs older than this number of days. Set 0 to disable auto-delete.',
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        ICP = self.env['ir.config_parameter'].sudo()
        res['webhook_log_retention_days'] = int(ICP.get_param(
            'tangerine_delivery_base.webhook_log_retention_days', default='30'
        ))
        return res

    def set_values(self):
        super().set_values()
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param(
            'tangerine_delivery_base.webhook_log_retention_days',
            str(self.webhook_log_retention_days)
        )
