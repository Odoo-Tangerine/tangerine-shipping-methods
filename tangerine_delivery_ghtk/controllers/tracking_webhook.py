import math
import logging
from odoo.tools import ustr
from odoo.http import request, Controller, route
from odoo.addons.tangerine_delivery_base.settings.utils import authentication, response
from odoo.addons.tangerine_delivery_base.settings.status import status

from ..settings.constants import settings

_logger = logging.getLogger(__name__)


class DeliveriesController(Controller):
    @authentication(settings.ghtk_code.value)
    @route(['/webhook/v1/delivery/ghtk', '/webhook/v1/delivery/ghtk/<string:access_token>'], type='json', auth='public', methods=['POST'])
    def ghtk_callback(self):
        try:
            body = request.dispatcher.jsonrequest
            _logger.info(f'WEBHOOK GHTK START - BODY: {body}')
            shipment_id = request.env['carrier.ref.order'].sudo().search([
                ('carrier_tracking_ref', '=', body.get('label_id'))
            ])
            if not shipment_id:
                _logger.error(f'WEBHOOK GHTK ERROR: The delivery id {body.get("label_id")} not found.')
                return response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The delivery id {body.get("label_id")} not found.'
                )
            if shipment_id.delivery_status_id.code in settings.block_webhook_change_status.value:
                _logger.error(
                    f'WEBHOOK GHTK ERROR: The delivery order {shipment_id.carrier_tracking_ref} is blocked')
                return response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The delivery order {shipment_id.carrier_tracking_ref} is blocked.'
                )
            status_id = request.env['delivery.status'].sudo().search([
                ('code', '=', body.get('status_id')),
                ('provider_id', '=', shipment_id.carrier_id.id)
            ])
            if not status_id:
                _logger.error(f'WEBHOOK GHTK ERROR: The status {body.get("status_id")} invalid.')
                return response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The status {body.get("status_id")} invalid.'
                )
            shipment_id.picking_id.sudo().write({'delivery_status_id': status_id.id})
            shipment_id.sudo().write({
                'real_delivery_charge': body.get('fee'),
                'real_weight': math.ceil(shipment_id.carrier_id.convert_weight(body.get('weight'), shipment_id.weight_unit))
            })
            _logger.info(f'WEBHOOK GHTK SUCCESS: Receive order callback {body.get("label_id")} successfully.')
            return response(
                status=status.HTTP_200_OK.value,
                message=f'Receive order callback {body.get("label_id")} successfully.'
            )
        except Exception as e:
            _logger.exception(f'WEBHOOK GHTK EXCEPTION: {ustr(e)}')
            return response(status=status.HTTP_500_INTERNAL_SERVER_ERROR.value, message=ustr(e))
