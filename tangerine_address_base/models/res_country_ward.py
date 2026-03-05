from odoo import models, fields, api
from ..static.utils import vietnamese_handler as vh


class Ward(models.Model):
    _name = 'res.country.ward'
    _description = 'ward'
    _order = 'name'

    code = fields.Char(string='Ward Code')
    name = fields.Char(string='Ward name')

    # outdated
    district_id = fields.Many2one(
        'res.country.district',
        string='District',
        domain="[('state_id', '=', state_id)]"
    )

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
        required=True,
        help="Type of the ward, commune."
    )
    ward_name_without_accent = fields.Char(
        string='Ward Name Without Accent',
        compute='_compute_ward_name_without_accent',
        store=True,
        help="Ward name without accent for easier searching."
    )
    active = fields.Boolean(default=True)

    _unique_name_code = models.Constraint(
        'unique(state_id, code, ward_type)', 'The code of the ward must be unique by state!'
    )

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

    @api.depends('name')
    def _compute_ward_name_without_accent(self):
        for rec in self:
            rec.ward_name_without_accent = vh.no_accent_vietnamese(rec.name) if rec.name else False