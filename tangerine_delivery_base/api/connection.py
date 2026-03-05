import requests
import logging
from dataclasses import dataclass
from odoo import _
from odoo.models import Model
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
_METHOD_DISPATCH = {'POST': lambda url, headers, kwargs: requests.post(url=url, headers=headers, json=kwargs), 'GET': lambda url, headers, kwargs: requests.get(url=url, headers=headers, params=kwargs), 'DELETE': lambda url, headers, kwargs: requests.delete(url=url, headers=headers, json=kwargs), 'PUT': lambda url, headers, kwargs: requests.put(url=url, headers=headers, data=kwargs), 'PATCH': lambda url, headers, kwargs: requests.patch(url=url, headers=headers, json=kwargs)}

@dataclass
class Connection:
    provider: Model
    endpoint: Model

    def __post_init__(self):
        self.debug = self.provider.log_xml

    def execute_restful(self, url, method, headers, **kwargs):
        try:
            _logger.warning('[%s] - [EXECUTE API]: %s: %s - Header: %s - Body: %s', self.provider.delivery_type.upper(), method, url, headers, kwargs)
            OOOOOO0OOO00O0OOO = _METHOD_DISPATCH.get(method)
            if not OOOOOO0OOO00O0OOO:
                self.debug(f'The interface not support method: {method}', url)
                raise UserError(_(f'The interface not support method: {method}'))
            OO0O0OO000OOO0O0O = OOOOOO0OOO00O0OOO(url, headers, kwargs)
            OO0O0OO000OOO0O0O.raise_for_status()
            if OO0O0OO000OOO0O0O.status_code == 204:
                self.debug('Successful', url)
                return True
            if not OO0O0OO000OOO0O0O.encoding:
                return OO0O0OO000OOO0O0O
            OOO0OO0OO00OOO0OO = OO0O0OO000OOO0O0O.json()
            _logger.info('RESULT EXECUTE API: %s', OOO0OO0OO00OOO0OO)
            self.debug(OOO0OO0OO00OOO0OO, url)
            return OOO0OO0OO00OOO0OO
        except UserError:
            raise
        except Exception as OO000O00OO00O0000:
            self.debug(str(OO000O00OO00O0000), url)
            raise UserError(str(OO000O00OO00O0000))