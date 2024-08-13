# -*- coding: utf-8 -*-
import json
import hmac
import time
import hashlib
import secrets
from dataclasses import dataclass
from odoo.tools.safe_eval import safe_eval
from odoo.addons.tangerine_delivery_base.api.connection import Connection
from odoo.addons.tangerine_delivery_base.settings.utils import URLBuilder

from ..settings.constants import settings


@dataclass
class Client:
    conn: Connection

    def _generate_signature(self, timestamp, payload, path_parameter):
        body_str = f'{timestamp}\r\n{self.conn.endpoint.method}'
        path = self.conn.endpoint.route
        if path_parameter:
            path = f'{path}/{path_parameter}'
        body_str += f'\r\n{path}'
        body_str += f'\r\n\r\n{json.dumps(payload or {})}' if self.conn.endpoint.code != settings.llm_get_cities_code.value else f'\r\n\r\n'
        return hmac.new(
            self.conn.provider.client_secret.encode(),
            body_str.encode(),
            hashlib.sha256
        ).hexdigest()

    def _generate_access_token(self, payload, path_parameter):
        timestamp = str(int(time.time() * 1000))
        return f'{self.conn.provider.api_key}:{timestamp}:{self._generate_signature(timestamp, payload, path_parameter)}'

    @staticmethod
    def _generate_nonce(length=16):
        timestamp = int(time.time() * 1e6)
        random_bits = secrets.token_hex(length)
        nonce = f'{timestamp:x}{random_bits}'
        return nonce

    def _builder_headers(self, payload, path_parameter):
        return {
            **json.loads(safe_eval(self.conn.endpoint.headers)),
            'Authorization': f'{self.conn.provider.token_type} {self._generate_access_token(payload, path_parameter)}',
            'Market': self.conn.provider.default_lalamove_regional_id.code,
            'Request-ID': self._generate_nonce()
        }

    def _execute(self, payload=None, path_parameter=None):
        return self.conn.execute_restful(
            url=URLBuilder.builder(
                host=self.conn.provider.domain,
                routes=[self.conn.endpoint.route],
                path_params=path_parameter
            ),
            headers=self._builder_headers(payload, path_parameter),
            method=self.conn.endpoint.method,
            **payload or {}
        )

    def get_cities(self): return self._execute()

    def get_quotation(self, payload): return self._execute(payload=payload)

    def place_order(self, payload): return self._execute(payload=payload)

    def cancel_order(self, order): return self._execute(path_parameter=order)

    def register_webhook(self, payload): return self._execute(payload=payload)
