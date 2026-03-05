import time
import logging

from odoo.http import request, Controller, route
from odoo.addons.tangerine_delivery_base.settings.utils import authentication, response
from odoo.addons.tangerine_delivery_base.settings.status import status
from ..settings.constants import settings

_logger = logging.getLogger(__name__)


class DeliveriesController(Controller):
    @authentication(settings.lalamove_code.value)
    @route(['/webhook/v1/delivery/lalamove', '/webhook/v1/delivery/lalamove/<string:access_token>'], type='jsonrpc', auth='public', methods=['POST'])
    def lalamove_callback(self):
        start_time = time.time()
        body = {}
        tracking_ref = ''
        carrier_id = None
        order_id = None
        try:
            body = request.dispatcher.jsonrequest
            _logger.info(f'WEBHOOK LALAMOVE START - BODY: {body}')
            if body.get('data') and body.get('data').get('order') and body.get('data').get('order').get('orderId'):
                tracking_ref = body.get('data').get('order').get('orderId')
            else:
                resp = response(
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY.value,
                    message=f'The delivery id is required.'
                )
                self._log_webhook('lalamove', body, '', resp, 'error',
                                  'Missing orderId in webhook body', start_time)
                return resp
            shipment_id = request.env['carrier.ref.order'].sudo().search([
                ('carrier_tracking_ref', '=', tracking_ref)
            ])
            if not shipment_id:
                _logger.error(f'WEBHOOK LALAMOVE ERROR: The delivery id {tracking_ref} not found.')
                resp = response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The delivery id {tracking_ref} not found.'
                )
                self._log_webhook('lalamove', body, tracking_ref, resp, 'error',
                                  f'Delivery id {tracking_ref} not found', start_time)
                return resp
            carrier_id = shipment_id.picking_id.carrier_id.id
            order_id = shipment_id.id
            if shipment_id.delivery_status_id.code in settings.block_webhook_change_status.value:
                _logger.error(
                    f'WEBHOOK LALAMOVE ERROR: The delivery order {shipment_id.carrier_tracking_ref} is blocked')
                resp = response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The delivery order {shipment_id.carrier_tracking_ref} is blocked.'
                )
                self._log_webhook('lalamove', body, tracking_ref, resp, 'ignored',
                                  'Status change blocked', start_time, carrier_id, order_id)
                return resp
            payload = {}
            if body.get('eventType') == settings.webhook_order_status_changed.value:
                if body.get('data') and body.get('data').get('order') and body.get('data').get('order').get('status'):
                    deliver_status = body.get('data').get('order').get('status')
                else:
                    resp = response(
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY.value,
                        message=f'The status is required.'
                    )
                    self._log_webhook('lalamove', body, tracking_ref, resp, 'error',
                                      'Missing status in webhook body', start_time, carrier_id, order_id)
                    return resp
                status_id = request.env['delivery.status'].sudo().search([
                    ('code', '=', deliver_status),
                    ('provider_id', '=', shipment_id.picking_id.carrier_id.id)
                ])
                if not status_id:
                    _logger.error(f'WEBHOOK LALAMOVE ERROR: The status {deliver_status} invalid.')
                    resp = response(
                        status=status.HTTP_400_BAD_REQUEST.value,
                        message=f'The status {deliver_status} invalid.'
                    )
                    self._log_webhook('lalamove', body, tracking_ref, resp, 'error',
                                      f'Invalid status: {deliver_status}', start_time, carrier_id, order_id)
                    return resp
                payload = {'delivery_status_id': status_id.id}
                if not shipment_id.picking_id.lalamove_tracking_link and body.get('data').get('order').get('shareLink'):
                    payload.update({'lalamove_tracking_link': body.get('data').get('order').get('shareLink')})
                shipment_id.picking_id.sudo().write(payload)
            if body.get('eventType') == settings.webhook_driver_assigned.value:
                if body.get('data').get('driver'):
                    payload.update({
                        'driver_name': body.get('data').get('driver').get('name'),
                        'driver_phone': body.get('data').get('driver').get('phone'),
                        'driver_license_plate': body.get('data').get('driver').get('plateNumber')
                    })
            if body.get('eventType') == settings.webhook_order_amount_changed.value:
                payload.update({'real_delivery_charge': body.get('data').get('balance').get('amount')})
            if payload:
                payload.pop('lalamove_tracking_link', None)
                shipment_id.sudo().write(payload)
            _logger.info(f'WEBHOOK LALAMOVE SUCCESS: Receive order callback {tracking_ref} successfully.')
            resp = response(
                status=status.HTTP_200_OK.value,
                message=f'Receive order callback {tracking_ref} successfully.'
            )
            self._log_webhook('lalamove', body, tracking_ref, resp, 'success',
                              None, start_time, carrier_id, order_id)
            return resp
        except Exception as e:
            _logger.exception(f'WEBHOOK LALAMOVE EXCEPTION: {str(e)}')
            resp = response(status=status.HTTP_500_INTERNAL_SERVER_ERROR.value, message=str(e))
            self._log_webhook('lalamove', body, tracking_ref, resp, 'error',
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
