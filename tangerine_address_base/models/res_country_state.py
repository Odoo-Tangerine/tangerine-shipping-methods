from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ..static.utils import vietnamese_handler as vh


class CountryState(models.Model):
    _inherit = 'res.country.state'

    district_ids = fields.One2many('res.country.district', 'state_id')

    external_code = fields.Char(
        string='External Code',
        help="A code used for external systems, such as shipping providers.",
    )
    state_type = fields.Selection(
        selection=[
            ('province', 'Province'),
            ('city', 'City'),
            ('capital', 'Capital'),
        ],
        string='State Type',
        default='province',
        help="Type of the state, province, or city."
    )
    state_name_without_accent = fields.Char(
        string='State Name Without Accent',
        compute='_compute_state_name_without_accent',
        store=True,
        help="State name without accent for easier searching."
    )
    active = fields.Boolean(default=True)
    ward_ids = fields.One2many(
        'res.country.ward',
        'state_id',
        string='Ward/Commune'
    )

    @api.constrains('external_code')
    def _check_external_code(self):
        for rec in self:
            if rec.country_id.code == 'VN' and not rec.external_code:
                raise ValidationError(
                    _('External code is required for Vietnam states.')
                )

    @api.constrains('state_type')
    def _check_state_type(self):
        for rec in self:
            if rec.country_id.code == 'VN' and not rec.state_type:
                raise ValidationError(
                    _('State type must be either "province" or "city" for Vietnam states.')
                )

    def _get_state_label(self):
        """ Get the translated product pricing unit label. """
        self.ensure_one()
        return dict(self._fields['state_type']._description_selection(self.env)).get(self.state_type)

    @api.depends_context('lang')
    @api.depends('name', 'state_type')
    def _compute_display_name(self):
        for rec in self:
            if rec.country_id.code != 'VN':
                rec.display_name = rec.name
            else:
                state_label = rec._get_state_label()
                if self.env.context.get('lang') == 'vi_VN':
                    rec.display_name = f'{state_label} {rec.name}'
                else:
                    rec.display_name = f'{vh.no_accent_vietnamese(rec.name)} {state_label}'

    @api.depends('name')
    def _compute_state_name_without_accent(self):
        for rec in self:
            rec.state_name_without_accent = vh.no_accent_vietnamese(rec.name)