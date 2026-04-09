# -*- coding: utf-8 -*-
import requests
import logging
from dataclasses import dataclass
from odoo import _
from odoo.models import Model
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

_METHOD_DISPATCH = {
    'POST': lambda url, headers, kwargs: requests.post(url=url, headers=headers, json=kwargs),
    'GET': lambda url, headers, kwargs: requests.get(url=url, headers=headers, params=kwargs),
    'DELETE': lambda url, headers, kwargs: requests.delete(url=url, headers=headers, json=kwargs),
    'PUT': lambda url, headers, kwargs: requests.put(url=url, headers=headers, data=kwargs),
    'PATCH': lambda url, headers, kwargs: requests.patch(url=url, headers=headers, json=kwargs),
}


@dataclass
class Connection:
    provider: Model
    endpoint: Model

    def __post_init__(self):
        self.debug = self.provider.log_xml

    def execute_restful(self, url, method, headers, **kwargs):
        try:
            _logger.warning(
                '[%s] - [EXECUTE API]: %s: %s - Header: %s - Body: %s',
                self.provider.delivery_type.upper(), method, url, headers, kwargs,
            )
            request_func = _METHOD_DISPATCH.get(method)
            if not request_func:
                self.debug(f'The interface not support method: {method}', url)
                raise UserError(_(f'The interface not support method: {method}'))
            response = request_func(url, headers, kwargs)
            response.raise_for_status()
            if response.status_code == 204:
                self.debug('Successful', url)
                return True
            if not response.encoding:
                return response
            result = response.json()
            _logger.info('RESULT EXECUTE API: %s', result)
            self.debug(result, url)
            return result
        except UserError:
            raise
        except Exception as e:
            self.debug(str(e), url)
            raise UserError(str(e))
