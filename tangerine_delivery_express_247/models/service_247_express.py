from odoo import fields, models
from odoo.addons.tangerine_delivery_base.settings.utils import get_route_api
from odoo.addons.tangerine_delivery_base.api.connection import Connection
from ..settings.constants import settings
from ..api.client import Client


class ServiceType247Express(models.Model):
    _name = 'service.type.247.express'
    _description = 'Service Type 247 Express'

    carrier_id = fields.Many2one(
        'delivery.carrier',
        string='Carrier',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(string='Name', required=True, readonly=True)
    code = fields.Char(string='Code', required=True, readonly=True)
    active = fields.Boolean(default=True)
    volumetric = fields.Integer(string='Volumetric')
    description = fields.Char(string='Description')

    def express_247_service_type_synchronous(self):
        carrier_id = self.env.ref('tangerine_delivery_express_247.tangerine_delivery_express_247_provider')
        client = Client(Connection(carrier_id, get_route_api(carrier_id, settings.get_service_type_route_code.value)))
        result = client.get_service_type()
        service_code = [rec.get('ServiceTypeID') for rec in result.get('ServiceTypes', [])]
        service_ids = self.search([('code', 'in', service_code)])
        services_existed = [rec.code for rec in service_ids]
        payload = []
        for rec in result.get('ServiceTypes', []):
            if rec.get('ServiceTypeID') not in services_existed:
                payload.append({
                    'carrier_id': carrier_id.id,
                    'name': rec.get('ServiceTypeName'),
                    'code': rec.get('ServiceTypeID'),
                    'volumetric': int(rec.get('CalculateVolumetric'))
                })
            else:
                service_id = service_ids.filtered(lambda line: line.code == rec.get('ServiceTypeID'))
                if service_id:
                    service_id.write({
                        'name': rec.get('ServiceTypeName'),
                        'code': rec.get('ServiceTypeID'),
                        'volumetric': int(rec.get('CalculateVolumetric'))
                    })
        if payload:
            self.create(payload)


class SpecialServiceType247Express(models.Model):
    _name = 'special.service.type.247.express'
    _description = 'Special Service Type 247 Express'

    carrier_id = fields.Many2one(
        'delivery.carrier',
        string='Carrier',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(string='Name', required=True, readonly=True)
    code = fields.Char(string='Code', required=True, readonly=True)
    active = fields.Boolean(default=True)
    description = fields.Char(string='Description')

    def express_247_special_service_type_synchronous(self):
        carrier_id = self.env.ref('tangerine_delivery_express_247.tangerine_delivery_express_247_provider')
        client = Client(Connection(carrier_id, get_route_api(carrier_id, settings.get_special_service_type_route_code.value)))
        result = client.get_special_service_type()
        service_code = [rec.get('ServiceID') for rec in result.get('Services', [])]
        service_ids = self.search([('code', 'in', service_code)])
        services_existed = [rec.code for rec in service_ids]
        payload = []
        for rec in result.get('Services', []):
            if rec.get('ServiceID') not in services_existed:
                payload.append({
                    'carrier_id': carrier_id.id,
                    'name': rec.get('ServiceName'),
                    'code': rec.get('ServiceID'),
                })
            else:
                service_id = service_ids.filtered(lambda line: line.code == rec.get('ServiceID'))
                if service_id:
                    service_id.write({
                        'name': rec.get('ServiceName'),
                        'code': rec.get('ServiceID'),
                    })
        if payload:
            self.create(payload)
