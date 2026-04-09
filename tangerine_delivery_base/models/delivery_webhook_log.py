import json
import time
import logging
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class DeliveryWebhookLog(models.Model):
    _name = 'delivery.webhook.log'
    _description = 'Delivery Webhook Log'
    _order = 'create_date desc'

    carrier_id = fields.Many2one(
        'delivery.carrier',
        string='Carrier',
        index=True,
        ondelete='set null',
    )
    carrier_type = fields.Char(
        string='Carrier Type',
        index=True,
        help='delivery_type of the carrier, e.g. ahamove, grab, lalamove',
    )
    tracking_ref = fields.Char(
        string='Tracking Ref',
        index=True,
        help='The carrier tracking reference extracted from the webhook body',
    )
    endpoint = fields.Char(string='Endpoint')
    http_method = fields.Char(string='HTTP Method', default='POST')
    request_headers = fields.Json(string='Request Headers')
    request_body = fields.Json(string='Request Body')
    response_body = fields.Json(string='Response Body')
    response_status = fields.Selection(
        selection=[
            ('success', 'Success'),
            ('error', 'Error'),
            ('ignored', 'Ignored'),
        ],
        string='Status',
        default='success',
        index=True,
    )
    error_message = fields.Text(string='Error Message')
    processing_time_ms = fields.Integer(
        string='Processing Time (ms)',
        help='Time taken to process the webhook in milliseconds',
    )
    ip_address = fields.Char(string='IP Address')
    order_id = fields.Many2one(
        'carrier.ref.order',
        string='Order',
        ondelete='set null',
    )

    @api.model
    def log_webhook(self, carrier_type, body, tracking_ref=None,
                    carrier_id=None, order_id=None, response_data=None,
                    response_status='success', error_message=None,
                    processing_time_ms=0):
        """Centralized method to create a webhook log entry.

        Can be called from any webhook controller after processing.
        """
        try:
            headers = {}
            endpoint = ''
            ip_address = ''
            http_method = 'POST'
            if request:
                httpreq = request.httprequest
                headers = dict(httpreq.headers)
                # Remove sensitive headers
                headers.pop('Cookie', None)
                headers.pop('Authorization', None)
                endpoint = httpreq.path
                ip_address = httpreq.remote_addr or ''
                http_method = httpreq.method or 'POST'

            vals = {
                'carrier_type': carrier_type,
                'tracking_ref': tracking_ref or '',
                'endpoint': endpoint,
                'http_method': http_method,
                'request_headers': headers,
                'request_body': body if isinstance(body, dict) else {},
                'response_body': response_data if isinstance(response_data, dict) else {},
                'response_status': response_status,
                'error_message': error_message or '',
                'processing_time_ms': processing_time_ms,
                'ip_address': ip_address,
            }
            if carrier_id:
                vals['carrier_id'] = carrier_id
            if order_id:
                vals['order_id'] = order_id

            self.sudo().create(vals)
        except Exception as e:
            # Never let logging failure break the webhook
            _logger.exception('Failed to create webhook log: %s', e)

    @api.model
    def _cron_cleanup_webhook_logs(self):
        """Scheduled action: delete webhook logs older than configured retention days."""
        ICP = self.env['ir.config_parameter'].sudo()
        retention_days = int(ICP.get_param(
            'tangerine_delivery_base.webhook_log_retention_days', '30'
        ))
        if retention_days <= 0:
            _logger.info('Webhook log auto-delete is disabled (retention_days=%s).', retention_days)
            return

        cutoff = fields.Datetime.now() - timedelta(days=retention_days)
        old_logs = self.sudo().search([('create_date', '<', cutoff)])
        count = len(old_logs)
        if count:
            old_logs.unlink()
            _logger.info('Webhook log cleanup: deleted %d logs older than %s days.', count, retention_days)
        else:
            _logger.info('Webhook log cleanup: no logs older than %s days to delete.', retention_days)
