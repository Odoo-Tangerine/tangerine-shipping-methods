import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.tangerine_delivery_base.settings.utils import get_route_api
from odoo.addons.tangerine_delivery_base.api.connection import Connection
from ..settings.constants import settings
from ..api.client import Client

_logger = logging.getLogger(__name__)


class ViettelPostService(models.Model):
    _name = 'viettelpost.service'
    _description = 'ViettelPost Service'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    extend_ids = fields.One2many('viettelpost.service.extend', 'service_id', string='Service Extend')

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'[{rec.code}] - {rec.name}'

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'Service already exists!'),
    ]

    def service_synchronous(self):
        viettelpost_carrier_id = self.env['delivery.carrier'].search([
            ('delivery_type', '=', settings.code.value)
        ])
        if not viettelpost_carrier_id:
            raise UserError(_('The carrier Viettelpost not found'))
        client = Client(Connection(
            viettelpost_carrier_id,
            get_route_api(viettelpost_carrier_id, settings.service_sync_route.value)
        ))
        result = client.service_synchronous()
        service_exists = [
            rec.code for rec in self.search([('code', 'in', [service.get('SERVICE_CODE') for service in result])])
        ]
        payload = []
        for service in result:
            if service.get('SERVICE_CODE') not in service_exists:
                payload.append({'code': service.get('SERVICE_CODE'), 'name': service.get('SERVICE_NAME')})
        if payload:
            unique_service = {item['code']: item for item in payload}
            self.create(list(unique_service.values()))


class ViettelPostServiceExtend(models.Model):
    _name = 'viettelpost.service.extend'
    _description = 'ViettelPost Service Extend'

    service_id = fields.Many2one('viettelpost.service', ondelete = 'cascade', required=True, string='Service')
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'[{rec.code}] - {rec.name}'

    _sql_constraints = [
        ('service_id_code_uniq', 'unique (service_id, code)', 'Service extend already exists!'),
    ]

    def service_extend_synchronous(self):
        viettelpost_carrier_id = self.env['delivery.carrier'].search([
            ('delivery_type', '=', settings.code.value)
        ])
        if not viettelpost_carrier_id:
            raise UserError(_('The carrier Viettelpost not found'))
        data = self.env['viettelpost.service'].search([])
        client = Client(Connection(
            viettelpost_carrier_id,
            get_route_api(viettelpost_carrier_id, settings.service_extend_sync_route.value)
        ))
        payload = []
        for rec in data:
            result = client.service_extend_synchronous(rec.code)
            service_exists = [
                rec.code for rec in self.search([
                    ('code', 'in', [service.get('SERVICE_CODE') for service in result]),
                    ('service_id', '=', rec.id)
                ])
            ]
            for service in result:
                if service.get('SERVICE_CODE') not in service_exists:
                    payload.append({
                        'service_id': rec.id,
                        'code': service.get('SERVICE_CODE'),
                        'name': service.get('SERVICE_NAME')
                    })
        if payload:
            self.create(payload)
