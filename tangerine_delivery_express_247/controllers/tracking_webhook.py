import logging
from odoo.tools import ustr
from odoo.http import request, Controller, route
from odoo.addons.tangerine_delivery_base.settings.status import status
from odoo.addons.tangerine_delivery_base.settings.utils import authentication, response

from ..settings.constants import settings

_logger = logging.getLogger(__name__)


class DeliveriesController(Controller):

    @authentication(settings.code.value)
    @route([
        '/webhook/v1/delivery/express_247',
        '/webhook/v1/delivery/express_247/<string:access_token>',
    ], type='json', auth='public', methods=['POST'])
    def express_247_callback(self):
        try:
            body = request.dispatcher.jsonrequest
            _logger.info(f'WEBHOOK 247 EXPRESS START - BODY: {body}')
            shipment_id = request.env['carrier.ref.order'].sudo().search([
                ('carrier_tracking_ref', '=', body.get('OrderCode'))
            ])
            if not shipment_id:
                _logger.error(f'WEBHOOK 247 EXPRESS ERROR: The delivery id {body.get("OrderCode")} not found.')
                return response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The delivery id {body.get("OrderCode")} not found.'
                )
            status_id = request.env['delivery.status'].sudo().search([
                ('code', '=', body.get('StatusName')),
                ('provider_id', '=', shipment_id.picking_id.carrier_id.id)
            ])
            if not status_id:
                _logger.error(f'WEBHOOK 247 EXPRESS ERROR: The status {body.get("StatusName")} invalid.')
                return response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The status {body.get("StatusName")} invalid.'
                )
            shipment_id.picking_id.sudo().write({'delivery_status_id': status_id.id})
            _logger.info(f'WEBHOOK 247 EXPRESS SUCCESS: Receive order callback {body.get("deliveryID")} successfully.')
            return response(
                status=status.HTTP_200_OK.value,
                message=f'Receive order callback {body.get("OrderCode")} successfully.'
            )
        except Exception as e:
            _logger.exception(f'WEBHOOK 247 EXPRESS EXCEPTION: {ustr(e)}')
            return response(status=status.HTTP_500_INTERNAL_SERVER_ERROR.value, message=ustr(e))
