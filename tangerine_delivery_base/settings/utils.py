# -*- coding: utf-8 -*-
import re
import pytz
import functools
from typing import NamedTuple, Any, Optional
from datetime import datetime
from urllib.parse import urlencode, unquote_plus
from odoo import _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.http import request
from .status import status


def response(status, message, data=None):
    response = {'status': status, 'message': message}
    if data:
        response.update({'data': data})
    return response


def authentication(carrier):
    def decorator(func):
        @functools.wraps(func)
        def wrap(self, *args, **kwargs):
            carrier_id = request.env['delivery.carrier'].sudo().search([('delivery_type', '=', carrier)])
            if not carrier_id:
                return response(
                    message=f'The {carrier} carrier not found.',
                    status=status.HTTP_404_NOT_FOUND.value
                )
            if carrier_id.is_use_authentication:
                token_sources = [
                    lambda: request.httprequest.headers.get('Authorization', '').replace('Bearer ', ''),
                    lambda: request.httprequest.args.get('access_token'),
                    lambda: kwargs.get('access_token')
                ]
                access_token = next((source() for source in token_sources if source()), None)
                if not access_token:
                    return response(
                        message='The access token is required',
                        status=status.HTTP_400_BAD_REQUEST.value
                    )
                if carrier_id.webhook_access_token != access_token:
                    return response(
                        message=f'The access token seems to have invalid.',
                        status=status.HTTP_401_UNAUTHORIZED.value
                    )
            request.update_env(SUPERUSER_ID)
            return func(self, *args, **kwargs)
        return wrap
    return decorator


def notification(notification_type, message):
    return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'type': notification_type,
            'message': _(message),
            'next': {'type': 'ir.actions.act_window_close'},
        }
    }


def get_route_api(provider_id, code):
    route_id = provider_id.route_api_ids.search([('code', '=', code)])
    if not route_id:
        raise UserError(_(f'Route {code} not found'))
    return route_id


def datetime_to_rfc3339(dt, time_zone):
    dt = dt.astimezone(pytz.timezone(time_zone))
    return dt.isoformat()


def datetime_to_iso_8601(dt):
    return datetime.strftime(dt, "%Y-%m-%dT%H:%M:%S.%fZ")


def rfc3339_to_datetime(dt):
    return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S.%fZ")


def standardization_e164(phone_number):
    phone_number = re.sub(r'[^\d+]', '', phone_number)
    if phone_number.startswith('0'):
        phone_number = f'84{phone_number[1:]}'
    elif phone_number.startswith('+'):
        phone_number = phone_number[1:]
    return phone_number


class URLBuilder(NamedTuple):
    host: str
    routes: str
    query_params: str
    path_params: str

    @classmethod
    def _add_path_params(cls, param_name, v=None):
        if not v: return v
        elif not isinstance(v, str): raise TypeError(f'{param_name} must be a str')
        return v

    @classmethod
    def _add_query_params(cls, param_name, v=None):
        if not v: return v
        elif not isinstance(v, dict): raise TypeError(f'{param_name} must be a dict')
        return urlencode(v)

    @classmethod
    def _add_routes(cls, param_name, v=None):
        if not v: return ''
        elif not isinstance(v, list): raise TypeError(f'{param_name} must be a list')
        return ''.join(v)

    @classmethod
    def _define_host(cls, param_name, v):
        if not v: raise KeyError(f'Key {param_name} missing')
        elif not isinstance(v, str): raise TypeError(f'Key {param_name} must be a string')
        return v

    @classmethod
    def to_url(cls, instance, is_unquote=None):
        url = f'{instance.host}{instance.routes}'
        if instance.path_params:
            url = f'{url}/{instance.path_params}'
        if instance.query_params:
            if is_unquote:
                params = re.sub(r"'", '"', unquote_plus(instance.query_params))
            else:
                params = re.sub(r"'", '"', instance.query_params)
            url = f'{url}?{params}'
        return url

    @classmethod
    def builder(cls, host, routes, query_params=None, path_params=None, is_unquote=None):
        instance = cls(
            cls._define_host('host', host),
            cls._add_routes('routes', routes),
            cls._add_query_params('query_params', query_params),
            cls._add_path_params('path_params', path_params),
        )
        return cls.to_url(instance, is_unquote)
