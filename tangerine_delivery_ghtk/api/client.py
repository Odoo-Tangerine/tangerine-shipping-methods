# -*- coding: utf-8 -*-
import json
from requests import Response
from dataclasses import dataclass
from odoo import _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError
from odoo.addons.tangerine_delivery_base.api.connection import Connection
from odoo.addons.tangerine_delivery_base.settings.utils import URLBuilder

from ..settings.constants import settings

@dataclass
class Client:
    conn: Connection

    def _build_headers(self):
        headers = json.loads(safe_eval(self.conn.endpoint.headers))
        if self.conn.endpoint.is_need_access_token:
            headers.update({'Token': self.conn.provider.api_key})
        return headers

    def _validate_response(self, result):
        if isinstance(result, Response) or result.get('success'):
            return result
        if self.conn.endpoint.code == settings.ghtk_check_xfast_service_route_code.value:
            raise UserError(_('The service XFast of GHTK unavailable. Please change service type to standard'))
        raise UserError(_(result.get('message', f'[GHTK]: Request {self.conn.endpoint.name} error')))

    def _execute(self, path_params=None, query_params=None, payload=None, is_unquote=True):
        return self._validate_response(
            self.conn.execute_restful(
                url=URLBuilder.builder(
                    host=self.conn.provider.domain,
                    routes=[self.conn.endpoint.route],
                    query_params=query_params,
                    path_params=path_params,
                    is_unquote=is_unquote
                ),
                headers=self._build_headers(),
                method=self.conn.endpoint.method,
                **payload or {}
            )
        )

    def estimate_order(self, params): return self._execute(query_params=params)

    def check_available_xfast_service(self, params): return self._execute(query_params=params)

    def create_order(self, payload): return self._execute(payload=payload)

    def cancel_order(self, carrier_tracking_ref): self._execute(path_params=carrier_tracking_ref)

    def print_order(self, carrier_tracking_ref, params):
        return self._execute(path_params=carrier_tracking_ref, query_params=params)
