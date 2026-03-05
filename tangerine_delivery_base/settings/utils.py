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
    OOOOOO0OOO00O0OOO = {'status': status, 'message': message}
    if data:
        OOOOOO0OOO00O0OOO.update({'data': data})
    return OOOOOO0OOO00O0OOO

def authentication(carrier):

    def decorator(func):

        @functools.wraps(func)
        def wrap(self, *args, **kwargs):
            OO0O0OO000OOO0O0O = request.env['delivery.carrier'].sudo().search([('delivery_type', '=', carrier)])
            if not OO0O0OO000OOO0O0O:
                return response(message=f'The {carrier} carrier not found.', status=status.HTTP_404_NOT_FOUND.value)
            if OO0O0OO000OOO0O0O.is_use_authentication:
                OOO0OO0OO00OOO0OO = [lambda: request.httprequest.headers.get('Authorization', '').replace('Bearer ', ''), lambda: request.httprequest.args.get('access_token'), lambda: kwargs.get('access_token')]
                OO000O00OO00O0000 = next((source() for source in OOO0OO0OO00OOO0OO if source()), None)
                if not OO000O00OO00O0000:
                    return response(message='The access token is required', status=status.HTTP_400_BAD_REQUEST.value)
                if OO0O0OO000OOO0O0O.webhook_access_token != OO000O00OO00O0000:
                    return response(message=f'The access token seems to have invalid.', status=status.HTTP_401_UNAUTHORIZED.value)
            request.update_env(SUPERUSER_ID)
            return func(self, *args, **kwargs)
        return wrap
    return decorator

def notification(notification_type, message):
    return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'type': notification_type, 'message': _(message), 'next': {'type': 'ir.actions.act_window_close'}}}

def get_route_api(provider_id, code):
    OO0O000000OOO0O00 = provider_id.route_api_ids.search([('code', '=', code)])
    if not OO0O000000OOO0O00:
        raise UserError(_(f'Route {code} not found'))
    return OO0O000000OOO0O00

def datetime_to_rfc3339(dt, time_zone):
    OO00O00O0OOOO0O0O = OO00O00O0OOOO0O0O.astimezone(pytz.timezone(time_zone))
    return OO00O00O0OOOO0O0O.isoformat()

def datetime_to_iso_8601(dt):
    return datetime.strftime(dt, '%Y-%m-%dT%H:%M:%S.%fZ')

def rfc3339_to_datetime(dt):
    return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%fZ')

def standardization_e164(phone_number):
    O00OOO00OOOO0O0O0 = re.sub('[^\\d+]', '', O00OOO00OOOO0O0O0)
    if O00OOO00OOOO0O0O0.startswith('0'):
        O00OOO00OOOO0O0O0 = f'84{O00OOO00OOOO0O0O0[1:]}'
    elif O00OOO00OOOO0O0O0.startswith('+'):
        O00OOO00OOOO0O0O0 = O00OOO00OOOO0O0O0[1:]
    return O00OOO00OOOO0O0O0

def convert_e164_to_classic(phone_number):
    O00O0O00000OO0000 = O00O0O00000OO0000.replace(' ', '')
    if re.match('^\\+84\\d{9,10}$', O00O0O00000OO0000):
        O00O0O00000OO0000 = f'0{O00O0O00000OO0000[3:]}'
    elif re.match('^84\\d{9,10}$', O00O0O00000OO0000):
        O00O0O00000OO0000 = f'0{O00O0O00000OO0000[2:]}'
    return O00O0O00000OO0000

class URLBuilder(NamedTuple):
    host: str
    routes: str
    query_params: str
    path_params: str

    @classmethod
    def _add_path_params(cls, param_name, v=None):
        if not v:
            return v
        elif not isinstance(v, str):
            raise TypeError(f'{param_name} must be a str')
        return v

    @classmethod
    def _add_query_params(cls, param_name, v=None):
        if not v:
            return v
        elif not isinstance(v, dict):
            raise TypeError(f'{param_name} must be a dict')
        return urlencode(v)

    @classmethod
    def _add_routes(cls, param_name, v=None):
        if not v:
            return ''
        elif not isinstance(v, list):
            raise TypeError(f'{param_name} must be a list')
        return ''.join(v)

    @classmethod
    def _define_host(cls, param_name, v):
        if not v:
            raise KeyError(f'Key {param_name} missing')
        elif not isinstance(v, str):
            raise TypeError(f'Key {param_name} must be a string')
        return v

    @classmethod
    def to_url(cls, instance, is_unquote=None):
        O0OOOOOOOOO00000O = f'{instance.host}{instance.routes}'
        if instance.path_params:
            O0OOOOOOOOO00000O = f'{O0OOOOOOOOO00000O}/{instance.path_params}'
        if instance.query_params:
            if is_unquote:
                O000OOOOOOOOOO000 = re.sub("'", '"', unquote_plus(instance.query_params))
            else:
                O000OOOOOOOOOO000 = re.sub("'", '"', instance.query_params)
            O0OOOOOOOOO00000O = f'{O0OOOOOOOOO00000O}?{O000OOOOOOOOOO000}'
        return O0OOOOOOOOO00000O

    @classmethod
    def builder(cls, host, routes, query_params=None, path_params=None, is_unquote=None):
        O00O00O000OOOOOOO = cls(cls._define_host('host', host), cls._add_routes('routes', routes), cls._add_query_params('query_params', query_params), cls._add_path_params('path_params', path_params))
        return cls.to_url(O00O00O000OOOOOOO, is_unquote)