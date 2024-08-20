# -*- coding: utf-8 -*-
import json
from dataclasses import dataclass
from odoo.tools.safe_eval import safe_eval
from odoo.addons.tangerine_delivery_base.api.connection import Connection
from odoo.addons.tangerine_delivery_base.settings.utils import URLBuilder


@dataclass
class Client:
    conn: Connection

    def _include_token(self, params):
        if self.conn.endpoint.is_need_access_token:
            params.update({'token': f'{self.conn.provider.access_token}'})
        return params

    def _execute(self, params, is_unquote=True):
        return self.conn.execute_restful(
            url=URLBuilder.builder(
                host=self.conn.provider.domain,
                routes=[self.conn.endpoint.route],
                query_params=self._include_token(params),
                is_unquote=is_unquote
            ),
            headers=json.loads(safe_eval(self.conn.endpoint.headers)),
            method=self.conn.endpoint.method
        )

    def get_access_token(self, params): return self._execute(params=params, is_unquote=False)

    def ahamove_service_synchronous(self, params): return self._execute(params=params, is_unquote=False)

    def estimate_order_fee(self, params): return self._execute(params=params)

    def create_order(self, params): return self._execute(params=params)

    def cancel_order(self, params): self._execute(params=params)
