import logging
from odoo.tools import ustr
from odoo.http import request, Controller, route
from odoo.addons.tangerine_delivery_base.settings.utils import authentication, response
from odoo.addons.tangerine_delivery_base.settings.status import status

from ..settings.constants import settings

_logger = logging.getLogger(__name__)


class DeliveriesController(Controller):
    @authentication(settings.grab_code.value)
    @route('/webhook/v1/delivery/grab', type='json', auth='public', methods=['POST'])
    def grab_callback(self):
        try:
            body = request.dispatcher.jsonrequest
            _logger.info(f'WEBHOOK GRAB START - BODY: {body}')
            shipment_id = request.env['carrier.ref.order'].sudo().search([
                ('carrier_tracking_ref', '=', body.get('deliveryID'))
            ])
            if not shipment_id:
                _logger.error(f'WEBHOOK GRAB ERROR: The delivery id {body.get("deliveryID")} not found.')
                return response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The delivery id {body.get("deliveryID")} not found.'
                )
            if shipment_id.delivery_status_id.code in settings.block_webhook_change_status.value:
                _logger.error(
                    f'WEBHOOK GHTK ERROR: The delivery order {shipment_id.carrier_tracking_ref} is blocked')
                return response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The delivery order {shipment_id.carrier_tracking_ref} is blocked.'
                )
            status_id = request.env['delivery.status'].sudo().search([
                ('code', '=', body.get('status')),
                ('provider_id', '=', shipment_id.carrier_id.id)
            ])
            if not status_id:
                _logger.error(f'WEBHOOK GRAB ERROR: The status {body.get("status")} invalid.')
                return response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The status {body.get("status")} invalid.'
                )
            payload = {'delivery_status_id': status_id.id}
            if not shipment_id.picking_id.grab_tracking_link:
                payload.update({'grab_tracking_link': body.get('trackURL')})
            shipment_id.picking_id.sudo().write(payload)
            if body.get('driver'):
                payload.update({
                    'driver_name': body.get('driver').get('name'),
                    'driver_phone': body.get('driver').get('phone'),
                    'driver_license_plate': body.get('driver').get('licensePlate'),
                })
            payload.pop('grab_tracking_link', None)
            shipment_id.sudo().write(payload)
            _logger.info(f'WEBHOOK GRAB SUCCESS: Receive order callback {body.get("deliveryID")} successfully.')
            return response(
                status=status.HTTP_200_OK.value,
                message=f'Receive order callback {body.get("deliveryID")} successfully.'
            )
        except Exception as e:
            _logger.exception(f'WEBHOOK GRAB EXCEPTION: {ustr(e)}')
            return response(status=status.HTTP_500_INTERNAL_SERVER_ERROR.value, message=ustr(e))
