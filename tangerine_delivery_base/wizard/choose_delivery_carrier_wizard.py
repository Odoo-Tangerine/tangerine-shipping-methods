from odoo import fields, models


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    is_cod = fields.Boolean(string='COD', default=False)
    cod_amount = fields.Monetary(string='Cash on delivery amount')