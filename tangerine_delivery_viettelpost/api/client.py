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

    def _build_header(self, token):
        headers = json.loads(safe_eval(self.conn.endpoint.headers))
        if self.conn.endpoint.code == settings.get_long_term_token_route.value and token:
            headers.update({'Token': token})
        elif self.conn.endpoint.is_need_access_token:
            headers.update({'Token': self.conn.provider.access_token})
        return headers

    def _validate_response(self, response):
        if response.get('error'):
            return response
        if self.conn.endpoint.code == settings.viettelpost_print_order_route.value:
            return response.get('message')
        return response.get('data')

    def _execute(self, params=None, payload=None, token=None):
        return self.conn.execute_restful(
            url=URLBuilder.builder(
                host=self.conn.provider.domain,
                routes=[self.conn.endpoint.route],
                query_params=params
            ),
            headers=self._build_header(token),
            method=self.conn.endpoint.method,
            **payload or {}
        )

    def get_short_term_access_token(self, payload):
        return self._validate_response(self._execute(payload=payload))

    def get_long_term_access_token(self, payload, token):
        return self._validate_response(self._execute(payload=payload, token=token))

    def service_synchronous(self):
        return self._validate_response(self._execute(payload={'TYPE': 2}))

    def service_extend_synchronous(self, extend_code):
        return self._validate_response(self._execute(params={'serviceCode': extend_code}))

    def estimate_cost(self, payload):
        return self._validate_response(self._execute(payload=payload))

    def create_order(self, payload):
        return self._validate_response(self._execute(payload=payload))

    def cancel_order(self, payload):
        self._execute(payload=payload)

    def print_order(self, payload):
        return self._validate_response(self._execute(payload=payload))
