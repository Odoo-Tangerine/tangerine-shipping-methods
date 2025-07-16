import logging
from odoo.tools import ustr
from odoo.http import request, Controller, route
from odoo.addons.tangerine_delivery_base.settings.utils import authentication, response
from odoo.addons.tangerine_delivery_base.settings.status import status

from ..settings.constants import settings

_logger = logging.getLogger(__name__)


class DeliveriesController(Controller):
    @authentication(settings.nhat_tin_code.value)
    @route('/webhook/v1/delivery/nhat_tin', type='json', auth='public', methods=['POST'])
    def grab_callback(self):
        try:
            body = request.dispatcher.jsonrequest
            _logger.info(f'WEBHOOK NHAT TIN LOGISTICS START - BODY: {body}')
            shipment_id = request.env['carrier.ref.order'].sudo().search([
                ('carrier_tracking_ref', '=', body.get('bill_no'))
            ])
            if not shipment_id:
                _logger.error(f'WEBHOOK NHAT TIN LOGISTICS ERROR: The delivery id {body.get("bill_no")} not found.')
                return response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The delivery id {body.get("bill_no")} not found.'
                )
            status_id = request.env['delivery.status'].sudo().search([
                ('code', '=', body.get('status_id')),
                ('provider_id', '=', shipment_id.picking_id.carrier_id.id)
            ])
            if not status_id:
                _logger.error(f'WEBHOOK NHAT TIN LOGISTICS ERROR: The status {body.get("status_id")} invalid.')
                return response(
                    status=status.HTTP_400_BAD_REQUEST.value,
                    message=f'The status {body.get("status_id")} invalid.'
                )
            shipment_id.picking_id.sudo().write({'delivery_status_id': status_id.id})
            shipment_id.sudo().write({
                'real_delivery_charge': body.get('shipping_fee'),
                'real_weight': body.get('dimension_weight', 0),
                'delivery_status_id': status_id.id
            })
            _logger.info(f'WEBHOOK NHAT TIN LOGISTICS SUCCESS: Receive order callback {body.get("bill_no")} successfully.')
            return response(
                status=status.HTTP_200_OK.value,
                message=f'Receive order callback {body.get("bill_no")} successfully.'
            )
        except Exception as e:
            _logger.exception(f'WEBHOOK NHAT TIN LOGISTICS EXCEPTION: {ustr(e)}')
            return response(status=status.HTTP_500_INTERNAL_SERVER_ERROR.value, message=ustr(e))
