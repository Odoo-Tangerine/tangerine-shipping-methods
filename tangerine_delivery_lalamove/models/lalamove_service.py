from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.addons.tangerine_delivery_base.settings.utils import get_route_api, notification
from odoo.addons.tangerine_delivery_base.api.connection import Connection
from ..settings.constants import settings
from ..api.client import Client


class LLMService(models.Model):
    _name = 'lalamove.service'
    _description = 'Lalamove Service'

    carrier_id = fields.Many2one(
        'delivery.carrier',
        required=True,
        ondelete='cascade',
        default=lambda self: self.env.ref('tangerine_delivery_lalamove.tangerine_delivery_lalamove_provider').id
    )
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Char(string='Description')
    special_service_ids = fields.One2many('lalamove.special.service', 'service_id')

    _sql_constraints = [
        ('uniq_code', 'unique(code)', 'Service must be unique')
    ]

    @staticmethod
    def _compute_service_name(word):
        lst_word_str = word.split('_')
        lst_word_str = [word.title() for word in lst_word_str]
        return ' '.join(lst_word_str)

    @staticmethod
    def _compute_special_service_name(word):
        lst_word_str = word.split('_')
        lst_word_str = [word.title() for word in lst_word_str]
        return ' '.join(lst_word_str)

    def llm_service_synchronous(self):
        carrier_id = self.env.ref('tangerine_delivery_lalamove.tangerine_delivery_lalamove_provider')
        if not carrier_id:
            raise UserError(_('The carrier Lalamove not found.'))
        elif not carrier_id.api_key:
            raise UserError(_('The field API Key of Lalamove not found.'))
        elif not carrier_id.client_secret:
            raise UserError(_('The field API Secret of Lalamove not found.'))
        client = Client(Connection(carrier_id, get_route_api(carrier_id, settings.llm_get_cities_code.value)))
        result = client.get_cities()
        for rec in result:
            lst_service_ids = self.search([('code', 'in', [service.get('key') for service in rec.get('services')])])
            lst_service_code = [rec.code for rec in lst_service_ids]
            lst_service_data = []
            for service in rec.get('services'):
                if service.get('key') not in lst_service_code:
                    dict_service_data = {
                        'name': self._compute_service_name(service.get('key')),
                        'code': service.get('key'),
                        'description': service.get('description'),
                        'special_service_ids': []
                    }
                    lst_spec_ids = self.env['lalamove.special.service'].search([
                        ('code', 'in', [spec.get('name') for spec in service.get('specialRequests')])
                    ])
                    lst_spec_code = [rec.code for rec in lst_spec_ids]
                    for spec in service.get('specialRequests'):
                        if spec.get('name') not in lst_spec_code:
                            dict_service_data['special_service_ids'].append((0, 0, {
                                'name': spec.get('description'),
                                'code': spec.get('name'),
                                'description': spec.get('description'),
                            }))
                    lst_service_data.append(dict_service_data)
            if lst_service_data:
                self.create(lst_service_data)


class LLMSpecialService(models.Model):
    _name = 'lalamove.special.service'
    _description = 'Lalamove Special Service'

    carrier_id = fields.Many2one(
        'delivery.carrier',
        required=True,
        ondelete='cascade',
        default=lambda self: self.env.ref('tangerine_delivery_lalamove.tangerine_delivery_lalamove_provider').id
    )
    name = fields.Char(string='Name', required=True)
    service_id = fields.Many2one('lalamove.service', string='Service', ondelete='cascade')
    code = fields.Char(string='Code', required=True)
    description = fields.Char(string='Description')

    _sql_constraints = [
        ('uniq_code', 'unique(service_id,code)', 'Special service must be unique')
    ]

