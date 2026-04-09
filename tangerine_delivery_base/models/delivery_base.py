import requests
from secrets import token_hex
from requests.exceptions import ConnectionError, ConnectTimeout
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from ..settings import utils


class DeliveryStandardStatus(models.Model):
    _name = 'delivery.standard.status'
    _description = 'Delivery Standard Status'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True, index=True)
    description = fields.Char(string='Description', translate=True)
    color = fields.Char(string='Color', default='#6c757d', help='Hex color code for dashboard card, e.g. #28a745')
    sequence = fields.Integer(string='Sequence', default=10)
    show_on_dashboard = fields.Boolean(string='Show on Dashboard', default=True)
    active = fields.Boolean(default=True)

    _unique_code = models.Constraint(
        'unique (code)', 'Standard status code must be unique.'
    )


class DeliveryBase(models.Model):
    _inherit = 'delivery.carrier'

    username = fields.Char(string='Username')
    password = fields.Char(string='Password')
    api_key = fields.Char(string='API Key')
    refresh_token = fields.Char(string='Refresh Token')
    partner_id = fields.Char(string='PartnerID')
    client_id = fields.Char(string='ClientID')
    client_secret = fields.Char(string='Client Secret')
    grant_type = fields.Char(string='Grant Type')
    scope = fields.Char(string='Scope')
    expire_token_date = fields.Datetime(string='Expire Token Date', readonly=True)

    image = fields.Binary(string='Icon image')
    access_token = fields.Char(string='Access Token')
    token_type = fields.Char(string='Token Type')
    domain = fields.Char(string='Domain')
    domain_printer = fields.Char(string='Domain Printer')
    route_api_ids = fields.One2many(
        'delivery.route.api',
        'provider_id',
        string='Routes API',
        context={'active_test': False}
    )
    status_ids = fields.One2many(
        'delivery.status',
        'provider_id',
        string='Status',
        context={'active_test': False}
    )
    base_weight_unit = fields.Selection(selection=[
        ('L', 'Pounds'),
        ('KG', 'Kilograms'),
        ('G', 'Grams')
    ], string='Weight Unit')
    default_promo_code = fields.Char(string='Promo Code')
    is_locally_delivery = fields.Boolean(string='Locally Delivery', default=False, readonly=True)
    is_support_multi_stop_delivery = fields.Boolean(string='Have Support for Multi-stop Delivery', default=False)
    is_use_authentication = fields.Boolean(string='Authentication', default=False)
    is_webhook_registered = fields.Boolean(string='Webhook Registered', default=False)
    is_support_feature_print_order = fields.Boolean(default=False)
    is_support_auto_cod_reconciliation = fields.Boolean(string='Support COD Reconciliation', default=False)
    status_mapping_ids = fields.One2many(
        'delivery.status.mapping',
        'provider_id',
        string='Status Mapping',
    )
    external_carrier_id = fields.Many2one('res.partner', string='Carrier')
    webhook_access_token = fields.Char(string='Webhook Access Token')
    webhook_url = fields.Char(string='URL')

    def convert_weight(self, weight, unit):
        if unit == 'KG':
            convert_to = 'uom.product_uom_kgm'
        elif unit == 'L':
            convert_to = 'uom.product_uom_lb'
        else:
            convert_to = 'uom.product_uom_gram'
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        new_value = weight_uom_id._compute_quantity(weight, self.env.ref(convert_to), round=False)
        if weight > 0.0:
            new_value = max(new_value, 0.01)
        return new_value

    @staticmethod
    def _compute_quantity(lines):
        quantity = 0
        for line in lines:
            if line._name == 'sale.order.line':
                quantity += line.product_uom_qty
            else:
                quantity += line.quantity
        return quantity

    def action_test_connection(self):
        self.ensure_one()
        try:
            if not self.domain:
                raise UserError(_('The field domain is required'))
            requests.get(self.domain, timeout=3)
            return utils.notification(
                notification_type='success',
                message=f'{self.domain} connection successfully'
            )
        except ConnectTimeout:
            return utils.notification(
                notification_type='danger',
                message=f'{self.domain} connection timeout'
            )
        except ConnectionError:
            return utils.notification(
                notification_type='danger',
                message=f'{self.domain} connection error'
            )

    def get_access_token(self):
        self.ensure_one()
        if not hasattr(self, f'{self.delivery_type}_get_access_token'):
            raise NotImplementedError(_(f'Subclass has no attributes {self.delivery_type}_get_access_token'))
        elif self.delivery_type in ['base_on_rule', 'fixed']:
            raise UserError(_('Get access token method does not support for provider has type Based on rules or Fixed Price'))
        return getattr(self, f'{self.delivery_type}_get_access_token')()

    def toggle_prod_environment(self):
        for carrier in self:
            carrier.prod_environment = not carrier.prod_environment
            if not hasattr(self, f'{self.delivery_type}_toggle_prod_environment'):
                raise NotImplementedError(_(f'Subclass has no attributes {self.delivery_type}_toggle_prod_environment'))
            getattr(self, f'{self.delivery_type}_toggle_prod_environment')()

    def action_generate_access_token(self):
        self.ensure_one()
        self.write({'webhook_access_token': token_hex()})

    def set_webhook_url(self):
        self.ensure_one()
        web_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        self.write({'webhook_url': f'{web_base_url}/webhook/v1/delivery/{self.delivery_type}'})

    def create_pdf_delivery_label(self, picking, content):
        return self.env['ir.attachment'].sudo().create([{
            'name': f'[{self.name}] - Delivery Label: {picking.carrier_tracking_ref}.pdf',
            'datas': content,
            'type': 'binary',
            'res_model': picking._name,
            'res_id': picking.id,
            'mimetype': 'application/pdf'
        }])

    def _get_default_rate_context(self, order):
        """Return a dict of context values needed for rate_shipment with default settings.

        Each carrier module should override this method to provide its specific
        defaults (service type, product type, payment method, etc.) so that
        rate_shipment can be called without manual wizard interaction.

        :param order: sale.order record
        :returns: dict of context keys
        """
        self.ensure_one()
        return {}

    def rate_shipment_with_defaults(self, order):
        """Call rate_shipment with automatic default context injection.

        This wraps rate_shipment() by first calling _get_default_rate_context()
        to gather carrier-specific defaults, then injecting them into context
        before calling rate_shipment(). This allows automated rate comparison
        without manual field selection in the wizard.

        :param order: sale.order record
        :returns: same dict as rate_shipment, with extra 'carrier_id' and 'carrier_name'
        """
        self.ensure_one()
        ctx = self._get_default_rate_context(order)
        try:
            result = self.with_context(**ctx).rate_shipment(order)
        except Exception as e:
            result = {
                'success': False,
                'price': 0.0,
                'error_message': str(e),
                'warning_message': False,
            }
        result['carrier_id'] = self.id
        result['carrier_name'] = self.name
        result['delivery_type'] = self.delivery_type
        return result

    def get_mapped_standard_status(self, carrier_status_id):
        """Get the mapped standard status record for a carrier status.

        Returns a delivery.standard.status record if mapping is found,
        otherwise returns an empty recordset.
        """
        self.ensure_one()
        if not carrier_status_id:
            return self.env['delivery.standard.status']
        mapping = self.status_mapping_ids.filtered(
            lambda m: m.carrier_status_id.id == carrier_status_id.id
        )
        return mapping[0].standard_status_id if mapping else self.env['delivery.standard.status']

    @staticmethod
    def common_payload_carrier_ref_order(picking, status, shipping_cost, carrier_tracking_ref):
        return {
            'picking_id': picking.id,
            'sale_id': picking.sale_id.id,
            'carrier_id': picking.carrier_id.id,
            'company_id': picking.company_id.id,
            'carrier_tracking_ref': carrier_tracking_ref,
            'remarks': picking.remarks,
            'cash_on_delivery': picking.cash_on_delivery,
            'cash_on_delivery_amount': picking.cash_on_delivery_amount,
            'schedule_order': picking.schedule_order,
            'schedule_pickup_time_from': picking.schedule_pickup_time_from,
            'schedule_pickup_time_to': picking.schedule_pickup_time_to,
            'promo_code': picking.promo_code,
            'delivery_status_id': status.id,
            'delivery_charge': shipping_cost,
            'real_delivery_charge': shipping_cost,
            'weight_unit': picking.carrier_id.base_weight_unit
        }


class DeliveryRouteAPI(models.Model):
    _name = 'delivery.route.api'
    _inherit = ['mail.thread']
    _description = 'Delivery Routes API'

    provider_id = fields.Many2one(
        'delivery.carrier',
        string='Provider',
        required=True,
        ondelete='cascade'
    )
    is_need_access_token = fields.Boolean(string='Need Access Token', default=False)
    domain = fields.Char(related='provider_id.domain', string='Domain')
    name = fields.Char(string='Name', tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True, index=True)
    route = fields.Char(string='Route', required=True, tracking=True)
    description = fields.Text(string='Description')
    method = fields.Selection([
        ('POST', 'POST'),
        ('DELETE', 'DELETE'),
        ('PUT', 'PUT'),
        ('GET', 'GET'),
        ('PATCH', 'PATCH')
    ], string='Method', required=True, tracking=True)
    active = fields.Boolean(default=True)
    headers = fields.Json(string='Headers', tracking=True)


class DeliveryStatus(models.Model):
    _name = 'delivery.status'
    _inherit = ['mail.thread']
    _description = 'Delivery Status'

    provider_id = fields.Many2one(
        'delivery.carrier',
        string='Provider',
        required=True,
        tracking=True,
        ondelete='cascade'
    )
    name = fields.Char(string='Name', tracking=True, required=True)
    code = fields.Char(string='Code', tracking=True, required=True)
    description = fields.Char(string='Description')
    standard_status_id = fields.Many2one(
        'delivery.standard.status',
        string='Standard Status',
        compute='_compute_standard_status_id',
        store=False,
    )

    _unique_provider_code = models.Constraint(
        'unique (provider_id,code)', 'Provider status code must be unique.'
    )

    def _compute_standard_status_id(self):
        """Compute standard status from mapping."""
        for record in self:
            mapping = self.env['delivery.status.mapping'].search([
                ('provider_id', '=', record.provider_id.id),
                ('carrier_status_id', '=', record.id),
            ], limit=1)
            record.standard_status_id = mapping.standard_status_id if mapping else False


class DeliveryStatusMapping(models.Model):
    _name = 'delivery.status.mapping'
    _description = 'Delivery Status Mapping'
    _rec_name = 'carrier_status_id'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    provider_id = fields.Many2one(
        'delivery.carrier',
        string='Provider',
        required=True,
        ondelete='cascade',
    )
    carrier_status_id = fields.Many2one(
        'delivery.status',
        string='Carrier Status',
        required=True,
        ondelete='cascade',
        domain="[('provider_id', '=', provider_id)]",
    )
    carrier_status_code = fields.Char(
        related='carrier_status_id.code',
        string='Carrier Code',
        store=True,
    )
    standard_status_id = fields.Many2one(
        'delivery.standard.status',
        string='Standard Status',
        required=True,
        ondelete='restrict',
    )

    _unique_mapping = models.Constraint(
        'unique (provider_id, carrier_status_id)',
        'Each carrier status can only be mapped once per provider.'
    )
