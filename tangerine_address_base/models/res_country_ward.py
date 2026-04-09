from odoo import models, fields, api
from ..static.utils import vietnamese_handler as vh


class Ward(models.Model):
    _name = 'res.country.ward'
    _description = 'Ward'

    code = fields.Char(string='Ward Code', readonly=True, required=True)
    name = fields.Char(string='Ward name', required=True)
    state_id = fields.Many2one(
        'res.country.state',
        string='State',
        required=True
    )
    ward_type = fields.Selection(
        selection=[
            ('ward', 'Ward'),
            ('commune', 'Commune'),
            ('special_zone', 'Special Zone'),
        ],
        string='Ward Type',
        default='ward',
        required = True,
        help="Type of the ward, commune."
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_code_uniq', 'unique(state_id, code, ward_type)', 'The code of the ward must be unique by state!')
    ]

    def _get_ward_label(self):
        """ Get the translated product pricing unit label. """
        self.ensure_one()
        return dict(self._fields['ward_type']._description_selection(self.env)).get(self.ward_type)

    @api.depends_context('lang')
    @api.depends('name', 'ward_type')
    def _compute_display_name(self):
        for rec in self:
            ward_label = rec._get_ward_label()
            if self.env.context.get('lang') == 'vi_VN':
                rec.display_name = f'{ward_label} {rec.name}'
            else:
                rec.display_name = f'{vh.no_accent_vietnamese(rec.name)} {ward_label}'
