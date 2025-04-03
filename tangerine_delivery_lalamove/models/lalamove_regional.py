from odoo import fields, models


class LLMRegional(models.Model):
    _name = 'lalamove.regional'
    _description = 'Lalamove Regional'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    lang = fields.Char(string='Language', required=True)

    _sql_constraints = [
        ('code_uniq', 'unique(name, code, lang)', 'Regional must be unique')
    ]
