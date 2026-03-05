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
    carrier_id = fields.Many2one('delivery.carrier', string='Carrier', index=True, ondelete='set null')
    carrier_type = fields.Char(string='Carrier Type', index=True, help='delivery_type of the carrier, e.g. ahamove, grab, lalamove')
    tracking_ref = fields.Char(string='Tracking Ref', index=True, help='The carrier tracking reference extracted from the webhook body')
    endpoint = fields.Char(string='Endpoint')
    http_method = fields.Char(string='HTTP Method', default='POST')
    request_headers = fields.Json(string='Request Headers')
    request_body = fields.Json(string='Request Body')
    response_body = fields.Json(string='Response Body')
    response_status = fields.Selection(selection=[('success', 'Success'), ('error', 'Error'), ('ignored', 'Ignored')], string='Status', default='success', index=True)
    error_message = fields.Text(string='Error Message')
    processing_time_ms = fields.Integer(string='Processing Time (ms)', help='Time taken to process the webhook in milliseconds')
    ip_address = fields.Char(string='IP Address')
    order_id = fields.Many2one('carrier.ref.order', string='Order', ondelete='set null')

    @api.model
    def log_webhook(self, carrier_type, body, tracking_ref=None, carrier_id=None, order_id=None, response_data=None, response_status='success', error_message=None, processing_time_ms=0):
        try:
            OOOOOO0OOO00O0OOO = {}
            OO0O0OO000OOO0O0O = ''
            OOO0OO0OO00OOO0OO = ''
            OO000O00OO00O0000 = 'POST'
            if request:
                OO0O000000OOO0O00 = request.httprequest
                OOOOOO0OOO00O0OOO = dict(OO0O000000OOO0O00.headers)
                OOOOOO0OOO00O0OOO.pop('Cookie', None)
                OOOOOO0OOO00O0OOO.pop('Authorization', None)
                OO0O0OO000OOO0O0O = OO0O000000OOO0O00.path
                OOO0OO0OO00OOO0OO = OO0O000000OOO0O00.remote_addr or ''
                OO000O00OO00O0000 = OO0O000000OOO0O00.method or 'POST'
            OO00O00O0OOOO0O0O = {'carrier_type': carrier_type, 'tracking_ref': tracking_ref or '', 'endpoint': OO0O0OO000OOO0O0O, 'http_method': OO000O00OO00O0000, 'request_headers': OOOOOO0OOO00O0OOO, 'request_body': body if isinstance(body, dict) else {}, 'response_body': response_data if isinstance(response_data, dict) else {}, 'response_status': response_status, 'error_message': error_message or '', 'processing_time_ms': processing_time_ms, 'ip_address': OOO0OO0OO00OOO0OO}
            if carrier_id:
                OO00O00O0OOOO0O0O['carrier_id'] = carrier_id
            if order_id:
                OO00O00O0OOOO0O0O['order_id'] = order_id
            self.sudo().create(OO00O00O0OOOO0O0O)
        except Exception as O00OOO00OOOO0O0O0:
            _logger.exception('Failed to create webhook log: %s', O00OOO00OOOO0O0O0)

    @api.model
    def _cron_cleanup_webhook_logs(self):
        O00O0O00000OO0000 = self.env['ir.config_parameter'].sudo()
        O0OOOOOOOOO00000O = int(O00O0O00000OO0000.get_param('tangerine_delivery_base.webhook_log_retention_days', '30'))
        if O0OOOOOOOOO00000O <= 0:
            _logger.info('Webhook log auto-delete is disabled (retention_days=%s).', O0OOOOOOOOO00000O)
            return
        O000OOOOOOOOOO000 = fields.Datetime.now() - timedelta(days=O0OOOOOOOOO00000O)
        O00O00O000OOOOOOO = self.sudo().search([('create_date', '<', O000OOOOOOOOOO000)])
        OOOO0O00O0O00000O = len(O00O00O000OOOOOOO)
        if OOOO0O00O0O00000O:
            O00O00O000OOOOOOO.unlink()
            _logger.info('Webhook log cleanup: deleted %d logs older than %s days.', OOOO0O00O0O00000O, O0OOOOOOOOO00000O)
        else:
            _logger.info('Webhook log cleanup: no logs older than %s days to delete.', O0OOOOOOOOO00000O)