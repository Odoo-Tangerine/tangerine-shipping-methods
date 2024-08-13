import logging
from odoo.tools import ustr
from odoo.http import request, Controller, route
from odoo.addons.tangerine_delivery_base.settings.utils import authentication, response
from odoo.addons.tangerine_delivery_base.settings.status import status

from ..settings.constants import settings

_logger = logging.getLogger(__name__)


class DeliveriesController(Controller):
    @authentication(settings.ahamove_code.value)
    @route('/webhook/v1/delivery/ahamove', type='json', auth='public', methods=['POST'])
    def ahamove_callback(self):
        try:
            body = request.dispatcher.jsonrequest
            _logger.info(f'WEBHOOK AHAMOVE START - BODY: {body}')
            shipment_id = request.env['carrier.ref.order'].sudo().search([
                ('carrier_tracking_ref', '=', body.get('_id'))
            ])
            if not shipment_id:
                _logger.error(f'WEBHOOK AHAMOVE ERROR: The delivery id {body.get("_id")} not found.')
                return response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The delivery id {body.get("_id")} not found.'
                )
            status_id = request.env['delivery.status'].sudo().search([
                ('code', '=', body.get('status')),
                ('provider_id', '=', shipment_id.picking_id.carrier_id.id)
            ])
            if not status_id:
                _logger.error(f'WEBHOOK AHAMOVE ERROR: The status {body.get("status")} invalid.')
                return response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The status {body.get("status")} invalid.'
                )
            payload = {'delivery_status_id': status_id.id}
            if not shipment_id.picking_id.ahamove_shared_link:
                payload.update({'ahamove_shared_link': body.get('shared_link')})
            if body.get('driver'):
                payload.update({
                    'driver_name': body.get('supplier_name'),
                    'driver_phone': body.get('supplier_id')
                })
            shipment_id.picking_id.sudo().write(payload)
            shipment_id.write({'real_delivery_charge': body.get('total_price')})
            _logger.info(f'WEBHOOK AHAMOVE SUCCESS: Receive order callback {body.get("_id")} successfully.')
            return response(
                status=status.HTTP_200_OK.value,
                message=f'Receive order callback {body.get("_id")} successfully.'
            )
        except Exception as e:
            _logger.exception(f'WEBHOOK AHAMOVE EXCEPTION: {ustr(e)}')
            return response(status=status.HTTP_500_INTERNAL_SERVER_ERROR.value, message=ustr(e))
