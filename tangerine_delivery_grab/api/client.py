# -*- coding: utf-8 -*-
import json
from dataclasses import dataclass
from odoo.tools.safe_eval import safe_eval
from odoo.addons.tangerine_delivery_base.settings.utils import (
    URLBuilder,
    datetime_to_rfc3339,
    standardization_e164
)
from odoo.addons.tangerine_delivery_base.api.connection import Connection


@dataclass
class Client:
    conn: Connection

    def _build_header(self):
        headers = json.loads(safe_eval(self.conn.endpoint.headers))
        if self.conn.endpoint.is_need_access_token:
            headers.update({'Authorization': f'{self.conn.provider.token_type} {self.conn.provider.access_token}'})
        return headers

    def _execute(self, payload=None, path_parameter=None):
        return self.conn.execute_restful(
            url=URLBuilder.builder(
                host=self.conn.provider.domain,
                routes=[self.conn.endpoint.route],
                path_params=path_parameter
            ),
            headers=self._build_header(),
            method=self.conn.endpoint.method,
            **payload or {}
        )

    def get_access_token(self, payload): return self._execute(payload=payload)

    def get_delivery_quotes(self, payload): return self._execute(payload=payload)

    def create_delivery_request(self, payload): return self._execute(payload=payload)

    def cancel_delivery(self, carrier_tracking_ref): self._execute(path_parameter=carrier_tracking_ref)
