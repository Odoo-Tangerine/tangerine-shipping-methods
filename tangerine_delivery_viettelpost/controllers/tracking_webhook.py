import time
import logging

from odoo.http import request, Controller, route
from odoo.addons.tangerine_delivery_base.settings.status import status
from odoo.addons.tangerine_delivery_base.settings.utils import authentication, response

from ..settings.constants import settings

_logger = logging.getLogger(__name__)


class DeliveriesController(Controller):

    @authentication(settings.code.value)
    @route('/webhook/v1/delivery/viettelpost', type='jsonrpc', auth='public', methods=['POST'])
    def viettelpost_callback(self):
        start_time = time.time()
        raw_body = {}
        tracking_ref = ''
        carrier_id = None
        order_id = None
        try:
            raw_body = request.dispatcher.jsonrequest
            _logger.info(f'WEBHOOK VIETTELPOST START - BODY: {raw_body}')
            body = raw_body.get('DATA')
            tracking_ref = body.get('ORDER_NUMBER', '') if body else ''
            shipment_id = request.env['carrier.ref.order'].sudo().search([
                ('carrier_tracking_ref', '=', tracking_ref)
            ])
            if not shipment_id:
                _logger.error(f'WEBHOOK VIETTELPOST ERROR: The delivery id {tracking_ref} not found.')
                resp = response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The delivery id {tracking_ref} not found.'
                )
                self._log_webhook('viettelpost', raw_body, tracking_ref, resp, 'error',
                                  f'Delivery id {tracking_ref} not found', start_time)
                return resp
            carrier_id = shipment_id.picking_id.carrier_id.id
            order_id = shipment_id.id
            status_id = request.env['delivery.status'].sudo().search([
                ('code', '=', body.get('ORDER_STATUS')),
                ('provider_id', '=', shipment_id.picking_id.carrier_id.id)
            ])
            if not status_id:
                _logger.error(f'WEBHOOK VIETTELPOST ERROR: The status {body.get("ORDER_STATUS")} invalid.')
                resp = response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The status {body.get("ORDER_STATUS")} invalid.'
                )
                self._log_webhook('viettelpost', raw_body, tracking_ref, resp, 'error',
                                  f'Invalid status: {body.get("ORDER_STATUS")}', start_time, carrier_id, order_id)
                return resp
            shipment_id.picking_id.sudo().write({'delivery_status_id': status_id.id})
            shipment_id.sudo().write({
                'real_delivery_charge': body.get('MONEY_TOTAL'),
                'real_weight': body.get('PRODUCT_WEIGHT', 0),
                'delivery_status_id': status_id.id
            })
            _logger.info(f'WEBHOOK VIETTELPOST SUCCESS: Receive order callback {tracking_ref} successfully.')
            resp = response(
                status=status.HTTP_200_OK.value,
                message=f'Receive order callback {tracking_ref} successfully.'
            )
            self._log_webhook('viettelpost', raw_body, tracking_ref, resp, 'success',
                              None, start_time, carrier_id, order_id)
            return resp
        except Exception as e:
            _logger.exception(f'WEBHOOK VIETTELPOST EXCEPTION: {str(e)}')
            resp = response(status=status.HTTP_500_INTERNAL_SERVER_ERROR.value, message=str(e))
            self._log_webhook('viettelpost', raw_body, tracking_ref, resp, 'error',
                              str(e), start_time, carrier_id, order_id)
            return resp

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
