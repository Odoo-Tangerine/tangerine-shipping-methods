import requests
from secrets import token_hex
from requests.exceptions import ConnectionError, ConnectTimeout
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError
from ..settings import utils


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
    ], string='Weight Unit', required=True)
    default_promo_code = fields.Char(string='Promo Code')
    is_locally_delivery = fields.Boolean(string='Locally Delivery', default=False)
    is_support_multi_stop_delivery = fields.Boolean(string='Have Support for Multi-stop Delivery', default=False)
    is_use_authentication = fields.Boolean(string='Authentication Use', default=False)
    is_webhook_registered = fields.Boolean(string='Webhook Registered', default=False)
    is_support_feature_print_order = fields.Boolean(default=False)
    webhook_access_token = fields.Char(string='Access Token')
    webhook_url = fields.Char(string='URL')

    @staticmethod
    def validate_human_information(human_ids):
        for human_id in human_ids:
            if not human_id.phone and not human_id.mobile:
                raise ValidationError(_(f'The phone number of {human_id.name} is required'))
            elif not human_id.state_id:
                raise ValidationError(_(f'The province of {human_id.name} is required'))
            elif not human_id.district_id:
                raise ValidationError(_(f'The district of {human_id.name} is required'))
            elif not human_id.ward_id:
                raise ValidationError(_(f'The ward of {human_id.name} is required'))
            elif not human_id.street:
                raise ValidationError(_(f'The street of {human_id.name} is required'))

    def send_shipping(self, pickings):
        self.ensure_one()
        if hasattr(self, f'{self.delivery_type}_send_shipping'):
            if self.is_locally_delivery:
                self.validate_human_information([pickings.picking_type_id.warehouse_id.partner_id, pickings.partner_id])
            return getattr(self, f'{self.delivery_type}_send_shipping')(pickings)

    def rate_shipment(self, order):
        self.ensure_one()
        if hasattr(self, f'{self.delivery_type}_rate_shipment'):
            if self.is_locally_delivery:
                self.validate_human_information([order.warehouse_id.partner_id, order.partner_shipping_id])
            res = getattr(self, f'{self.delivery_type}_rate_shipment')(order)
            # apply fiscal position
            company = self.company_id or order.company_id or self.env.company
            res['price'] = self.product_id._get_tax_included_unit_price(
                company,
                company.currency_id,
                order.date_order,
                'sale',
                fiscal_position=order.fiscal_position_id,
                product_price_unit=res['price'],
                product_currency=company.currency_id
            )
            # apply margin on computed price
            res['price'] = float(res['price']) * (1.0 + self.margin) + self.fixed_margin
            # save the real price in case a free_over rule overide it to 0
            res['carrier_price'] = res['price']
            # free when order is large enough
            amount_without_delivery = order._compute_amount_total_without_delivery()
            if res['success'] and self.free_over and self._compute_currency(order, amount_without_delivery, 'pricelist_to_company') >= self.amount:
                res['warning_message'] = _('The shipping is free since the order amount exceeds %.2f.', self.amount)
                res['price'] = 0.0
            return res

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
        return self.env['ir.attachment'].sudo().create({
            'name': f'[{self.name}] - Delivery Label: {picking.carrier_tracking_ref}.pdf',
            'datas': content,
            'type': 'binary',
            'res_model': picking._name,
            'res_id': picking.id,
            'mimetype': 'application/pdf'
        })


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

    _sql_constraints = [
        ('provider_code_uniq', 'unique(provider_id,code)', 'Provider status code must be unique.'),
    ]
