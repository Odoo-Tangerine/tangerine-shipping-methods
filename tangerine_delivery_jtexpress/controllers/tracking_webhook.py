# -*- coding: utf-8 -*-
import json
import time
import logging

from odoo.http import request, Controller, route, Response
from odoo.addons.tangerine_delivery_base.settings.utils import authentication

from ..settings.constants import settings

_logger = logging.getLogger(__name__)


class JTExpressWebhookController(Controller):
    """
    J&T Express Webhook Endpoint.

    J&T Express pushes logistics status updates to this URL via:
        POST application/x-www-form-urlencoded
        Headers: apiAccount, digest, timestamp  (J&T's own auth – informational)
        Body:    bizContent = JSON string

    bizContent format:
        {
            "billCode": "JT1234567890",
            "txlogisticId": "SO/00001",
            "details": [
                {
                    "scanTime": "2024-06-05 15:57:04",
                    "desc": "...",
                    "scanTypeCode": 113,
                    "scanTypeName": "Ký nhận",
                    ...
                }
            ]
        }

    Expected response (J&T checks this):
        {"code": "1", "msg": "success", "data": null}
    """

    @staticmethod
    def _jtexpress_response(code='1', msg='success', data=None):
        return Response(
            json.dumps({'code': code, 'msg': msg, 'data': data}),
            content_type='application/json; charset=utf-8',
            status=200,
        )

    @authentication(settings.code.value)
    @route('/webhook/v1/delivery/jtexpress', type='http', auth='public', methods=['POST'], csrf=False)
    def jtexpress_callback(self, **kwargs):
        start_time = time.time()
        raw_biz_content = ''
        biz_content = {}
        tracking_ref = ''
        carrier_id = None
        order_id = None

        try:
            # J&T sends form-encoded body; bizContent is a JSON string
            raw_biz_content = request.httprequest.form.get('bizContent', '')
            _logger.info('WEBHOOK JTEXPRESS START - raw bizContent: %s', raw_biz_content)

            if not raw_biz_content:
                resp_data = {'code': '0', 'msg': 'Missing bizContent', 'data': None}
                self._log_webhook(settings.code.value, {}, '', resp_data, 'error',
                                  'Missing bizContent', start_time)
                return self._jtexpress_response('0', 'Missing bizContent')

            biz_content = json.loads(raw_biz_content)
            tracking_ref = biz_content.get('billCode') or ''

            if not tracking_ref:
                _logger.error('WEBHOOK JTEXPRESS ERROR: Missing billCode in bizContent.')
                resp_data = {'code': '0', 'msg': 'Missing billCode', 'data': None}
                self._log_webhook(settings.code.value, biz_content, '', resp_data, 'error',
                                  'Missing billCode', start_time)
                return self._jtexpress_response('0', 'Missing billCode')

            shipment_id = request.env['carrier.ref.order'].sudo().search([
                ('carrier_tracking_ref', '=', tracking_ref)
            ], limit=1)

            if not shipment_id:
                _logger.error('WEBHOOK JTEXPRESS ERROR: Delivery %s not found.', tracking_ref)
                resp_data = {'code': '0', 'msg': f'Delivery {tracking_ref} not found', 'data': None}
                self._log_webhook(settings.code.value, biz_content, tracking_ref, resp_data,
                                  'error', f'Delivery {tracking_ref} not found', start_time)
                return self._jtexpress_response('0', f'Delivery {tracking_ref} not found')

            carrier_id = shipment_id.picking_id.carrier_id.id
            order_id = shipment_id.id

            # Get the latest scanTypeCode from the first detail entry
            details = biz_content.get('details') or []
            scan_type_code = None
            if details and isinstance(details, list):
                scan_type_code = details[0].get('scanTypeCode')

            if scan_type_code is None:
                _logger.warning('WEBHOOK JTEXPRESS: No scanTypeCode in details for %s.', tracking_ref)
                resp_data = {'code': '1', 'msg': 'success', 'data': None}
                self._log_webhook(settings.code.value, biz_content, tracking_ref, resp_data,
                                  'success', None, start_time, carrier_id, order_id)
                return self._jtexpress_response()

            # Map scanTypeCode → our delivery.status code
            scan_map = settings.scan_type_code_to_status.value
            status_code = scan_map.get(int(scan_type_code))

            if not status_code:
                _logger.warning('WEBHOOK JTEXPRESS: Unknown scanTypeCode %s for %s.', scan_type_code, tracking_ref)
                resp_data = {'code': '1', 'msg': 'success', 'data': None}
                self._log_webhook(settings.code.value, biz_content, tracking_ref, resp_data,
                                  'success', f'Unknown scanTypeCode: {scan_type_code}', start_time, carrier_id, order_id)
                return self._jtexpress_response()

            status_id = request.env['delivery.status'].sudo().search([
                ('code', '=', status_code),
                ('provider_id', '=', carrier_id)
            ], limit=1)

            if not status_id:
                _logger.error('WEBHOOK JTEXPRESS ERROR: Status %s not found for carrier %s.', status_code, carrier_id)
                resp_data = {'code': '0', 'msg': f'Status {status_code} not recognised', 'data': None}
                self._log_webhook(settings.code.value, biz_content, tracking_ref, resp_data, 'error',
                                  f'Invalid status: {status_code}', start_time, carrier_id, order_id)
                return self._jtexpress_response('0', f'Status {status_code} not recognised')

            # Update picking and carrier.ref.order
            shipment_id.picking_id.sudo().write({'delivery_status_id': status_id.id})
            shipment_id.sudo().write({
                'delivery_status_id': status_id.id,
            })

            _logger.info('WEBHOOK JTEXPRESS SUCCESS: %s updated to scanTypeCode=%s → %s.',
                         tracking_ref, scan_type_code, status_code)
            resp_data = {'code': '1', 'msg': 'success', 'data': None}
            self._log_webhook(settings.code.value, biz_content, tracking_ref, resp_data,
                              'success', None, start_time, carrier_id, order_id)
            return self._jtexpress_response()

        except json.JSONDecodeError as e:
            _logger.exception('WEBHOOK JTEXPRESS: Invalid JSON in bizContent: %s', str(e))
            resp_data = {'code': '0', 'msg': f'Invalid JSON: {e}', 'data': None}
            self._log_webhook(settings.code.value, {'raw': raw_biz_content}, tracking_ref,
                              resp_data, 'error', str(e), start_time, carrier_id, order_id)
            return self._jtexpress_response('0', f'Invalid JSON: {e}')

        except Exception as e:
            _logger.exception('WEBHOOK JTEXPRESS EXCEPTION: %s', str(e))
            resp_data = {'code': '0', 'msg': str(e), 'data': None}
            self._log_webhook(settings.code.value, biz_content, tracking_ref,
                              resp_data, 'error', str(e), start_time, carrier_id, order_id)
            return self._jtexpress_response('0', str(e))

    @staticmethod
    def _log_webhook(carrier_type, body, tracking_ref, resp, resp_status,
                     error_msg, start_time, carrier_id=None, order_id=None):
        elapsed = int((time.time() - start_time) * 1000)
        request.env['delivery.webhook.log'].sudo().log_webhook(
            carrier_type=carrier_type,
            body=body,
            tracking_ref=tracking_ref,
            carrier_id=carrier_id,
            order_id=order_id,
            response_data=resp,
            response_status=resp_status,
            error_message=error_msg,
            processing_time_ms=elapsed,
        )
