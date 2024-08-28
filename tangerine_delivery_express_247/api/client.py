# -*- coding: utf-8 -*-
import json
from dataclasses import dataclass
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError
from odoo.addons.tangerine_delivery_base.settings.utils import URLBuilder
from odoo.addons.tangerine_delivery_base.api.connection import Connection
from ..settings.constants import settings


@dataclass
class Client:
    conn: Connection

    def _build_header(self):
        headers = json.loads(safe_eval(self.conn.endpoint.headers))
        if self.conn.endpoint.is_need_access_token:
            headers.update({
                'token': self.conn.provider.access_token,
                'ClientID': self.conn.provider.client_id
            })
        return headers

    @staticmethod
    def _validate_response(response):
        if response.get('IsError') or response.get('ErrorMessage'):
            raise UserError(response.get('ErrorMessage'))
        return response

    def _execute(self, payload=None):
        return self.conn.execute_restful(
            url=URLBuilder.builder(
                host=self.conn.provider.domain,
                routes=[self.conn.endpoint.route]
            ),
            headers=self._build_header(),
            method=self.conn.endpoint.method,
            **payload or {}
        )

    def get_access_token(self, payload): return self._validate_response(self._execute(payload=payload))

    def get_service_type(self): return self._validate_response(self._execute())

    def get_special_service_type(self): return self._validate_response(self._execute())

    def get_hubs(self, payload): return self._validate_response(self._execute(payload=payload))

    def create_hub(self, payload): return self._validate_response(self._execute(payload=payload))

    def update_hub(self, payload): return self._validate_response(self._execute(payload=payload))

    def get_price(self, payload): return self._validate_response(self._execute(payload=payload))

    def create_order(self, payload): return self._validate_response(self._execute(payload=payload))

    def cancel_order(self, payload): self._execute(payload=payload)

    def print_order(self, payload): return self._validate_response(self._execute(payload=payload))
