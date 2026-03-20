# -*- coding: utf-8 -*-
import json
import hashlib
import base64
import time
import requests
import logging
from dataclasses import dataclass
from odoo.exceptions import UserError
from odoo.addons.tangerine_delivery_base.settings.utils import URLBuilder

_logger = logging.getLogger(__name__)


@dataclass
class Client:
    """
    J&T Express Vietnam API Client.

    Authentication scheme (all requests):
    - Method  : POST
    - Encoding: application/x-www-form-urlencoded
    - Headers : apiAccount, digest, timestamp (milliseconds UTC+7)
    - Body    : bizContent = JSON-string of business payload

    Digest formula:
        digest = base64( md5_bytes( bizContent_json + privateKey ) )
        Note: md5() must return the raw byte array, then base64-encode those bytes.
    """

    provider: object  # delivery.carrier recordset

    # ------------------------------------------------------------------ #
    # Authentication helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _compute_digest(biz_content_str: str, private_key: str) -> str:
        """
        Compute: base64( MD5_bytes( bizContent_json_string + privateKey ) )
        """
        raw = biz_content_str + private_key
        md5_bytes = hashlib.md5(raw.encode('utf-8')).digest()
        return base64.b64encode(md5_bytes).decode('utf-8')

    def _build_headers(self, biz_content_str: str) -> dict:
        if not self.provider.jtexpress_api_account:
            raise UserError('J&T Express: API Account (apiAccount) chưa được cấu hình.')
        if not self.provider.api_key:
            raise UserError('J&T Express: Private Key chưa được cấu hình.')

        # Timestamp in milliseconds (UTC+7 epoch ms — same numeric value as UTC)
        timestamp = int(time.time() * 1000)
        digest = self._compute_digest(biz_content_str, self.provider.api_key)

        return {
            'apiAccount': str(self.provider.jtexpress_api_account),
            'digest': digest,
            'timestamp': str(timestamp),
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
        }

    def _validate_credentials(self):
        missing = []
        if not self.provider.jtexpress_customer_code:
            missing.append('Customer Code (customerCode)')
        if not self.provider.jtexpress_password:
            missing.append('Customer Password')
        if missing:
            raise UserError('J&T Express: Thiếu thông tin cấu hình: %s' % ', '.join(missing))

    # ------------------------------------------------------------------ #
    # Core execute
    # ------------------------------------------------------------------ #

    def _get_url(self, route: str) -> str:
        return URLBuilder.builder(
            host=self.provider.domain,
            routes=[route],
        )

    def _execute(self, route: str, payload: dict) -> dict:
        """
        Serialize payload → bizContent JSON string, compute digest, POST.
        """
        biz_content_str = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
        url = self._get_url(route)
        headers = self._build_headers(biz_content_str)
        form_data = {'bizContent': biz_content_str}

        _logger.warning('[JTEXPRESS] POST %s | bizContent: %s', url, biz_content_str)

        try:
            resp = requests.post(url=url, headers=headers, data=form_data, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            _logger.info('[JTEXPRESS] RESPONSE: %s', result)
            return result
        except Exception as e:
            raise UserError(str(e))

    def _validate_response(self, response: dict) -> dict:
        """
        J&T standard response format:
            { "code": "1", "msg": "success", "data": { ... } }

        code == "1"  → success
        anything else → error; raise UserError with the msg field.
        """
        if not isinstance(response, dict):
            raise UserError('J&T Express: Định dạng phản hồi không hợp lệ.')

        code = str(response.get('code', ''))
        if code != '1':
            msg = response.get('msg') or 'J&T Express API error.'
            raise UserError(f'J&T Express [{code}]: {msg}')

        data = response.get('data')
        if isinstance(data, list) and data:
            return data[0]
        return data or {}

    # ------------------------------------------------------------------ #
    # Route helper
    # ------------------------------------------------------------------ #

    def _get_route(self, code: str) -> str:
        route = self.provider.route_api_ids.filtered(lambda r: r.code == code)
        if not route:
            raise UserError(f'J&T Express: Route với code "{code}" không tìm thấy. '
                            f'Vui lòng kiểm tra cấu hình Route API.')
        return route[0].route

    # ------------------------------------------------------------------ #
    # Public API methods
    # ------------------------------------------------------------------ #

    def create_order(self, payload: dict) -> dict:
        """POST /api/order/addOrder"""
        self._validate_credentials()
        route = self._get_route('jtexpress_create_order')
        result = self._execute(route, payload)
        return self._validate_response(result)

    def cancel_order(self, payload: dict) -> dict:
        """POST /api/order/cancelOrder"""
        self._validate_credentials()
        route = self._get_route('jtexpress_cancel_order')
        result = self._execute(route, payload)
        return self._validate_response(result)

    def track_order(self, payload: dict) -> dict:
        """POST /api/logistics/trace"""
        self._validate_credentials()
        route = self._get_route('jtexpress_track_order')
        result = self._execute(route, payload)
        return self._validate_response(result)

    def estimate_cost(self, payload: dict) -> dict:
        """POST /api/spmComCost/getComCost"""
        self._validate_credentials()
        route = self._get_route('jtexpress_estimate_cost')
        result = self._execute(route, payload)
        return self._validate_response(result)

    def print_label(self, payload: dict) -> dict:
        """POST /api/order/printOrder — returns base64-encoded label content"""
        self._validate_credentials()
        route = self._get_route('jtexpress_print_label')
        result = self._execute(route, payload)
        return self._validate_response(result)
