from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import ustr
from odoo.addons.tangerine_delivery_base.settings.utils import get_route_api
from ..settings.constants import settings
from odoo.addons.tangerine_delivery_base.api.connection import Connection
from ..api.client import Client


class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    express_247_hub_id = fields.Id(string='HubID', readonly=True)
