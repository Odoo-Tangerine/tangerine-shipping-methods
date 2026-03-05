from odoo import api, fields, models, _
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict

class DeliveryDashboard(models.AbstractModel):
    _name = 'delivery.dashboard'
    _description = 'Delivery Dashboard'
    _auto = False

    @api.model
    def get_dashboard_data(self, date_from=None, date_to=None, carrier_id=None):
        OOOOOO0OOO00O0OOO = date.today()
        if not date_from:
            date_from = OOOOOO0OOO00O0OOO.replace(day=1)
        else:
            date_from = fields.Date.from_string(date_from)
        if not date_to:
            date_to = OOOOOO0OOO00O0OOO
        else:
            date_to = fields.Date.from_string(date_to)
        OO000O00OO00O0000 = [('create_date', '>=', fields.Datetime.to_string(date_from)), ('create_date', '<=', fields.Datetime.to_string(date_to + timedelta(days=1)))]
        if carrier_id:
            OO000O00OO00O0000.append(('carrier_id', '=', carrier_id))
        OO0O000000OOO0O00 = [('create_date', '>=', fields.Datetime.to_string(date_from)), ('create_date', '<=', fields.Datetime.to_string(date_to + timedelta(days=1)))]
        if carrier_id:
            OO0O000000OOO0O00.append(('carrier_id', '=', carrier_id))
        OO00O00O0OOOO0O0O = {'currency_symbol': self.env.company.currency_id.symbol or '', 'currency_code': self.env.company.currency_id.name or 'VND', 'currency_position': self.env.company.currency_id.position or 'after', 'kpi': self._get_kpi_data(OO000O00OO00O0000), 'carrier_breakdown': self._get_carrier_breakdown(OO000O00OO00O0000), 'daily_orders': self._get_daily_orders(OO000O00OO00O0000, date_from, date_to), 'status_distribution': self._get_status_distribution(OO000O00OO00O0000), 'cost_comparison': self._get_cost_comparison(OO000O00OO00O0000), 'cod_summary': self._get_cod_summary(OO000O00OO00O0000), 'carriers': self._get_carriers_list(), 'webhook_stats': self._get_webhook_stats(OO0O000000OOO0O00, date_from, date_to), 'performance': self._get_performance_analytics(OO000O00OO00O0000, date_from, date_to), 'standard_status_cards': self._get_standard_status_cards(OO000O00OO00O0000)}
        return OO00O00O0OOOO0O0O

    @api.model
    def _get_kpi_data(self, domain):
        O00OOO00OOOO0O0O0 = self.env['carrier.ref.order']
        O00O0O00000OO0000 = O00OOO00OOOO0O0O0.search(domain)
        O0OOOOOOOOO00000O = len(O00O0O00000OO0000)
        O000OOOOOOOOOO000 = sum(O00O0O00000OO0000.mapped('delivery_charge'))
        O00O00O000OOOOOOO = sum(O00O0O00000OO0000.mapped('real_delivery_charge'))
        OOOO0O00O0O00000O = sum(O00O0O00000OO0000.filtered('cash_on_delivery').mapped('cash_on_delivery_amount'))
        O00OOO0OO0OOO0OOO = len(O00O0O00000OO0000.filtered('cash_on_delivery'))
        OO00O0O0OO0OOO0OO = ['501', 'COMPLETED', '6']
        O0000O000OOO00OO0 = ['503', 'CANCELED', 'REJECTED', 'EXPIRED', '-1', 'CANCELLED']
        O0O0000O0OOOO00OO = 0
        OOO000OOO00OOOO00 = 0
        for O0O0OO0O00OO0O0OO in O00O0O00000OO0000:
            if O0O0OO0O00OO0O0OO.mapped_status_id:
                if O0O0OO0O00OO0O0OO.mapped_status_id.code == 'delivered':
                    O0O0000O0OOOO00OO += 1
                elif O0O0OO0O00OO0O0OO.mapped_status_id.code in ('cancelled', 'failed'):
                    OOO000OOO00OOOO00 += 1
            elif O0O0OO0O00OO0O0OO.delivery_status_id.code in OO00O0O0OO0OOO0OO:
                O0O0000O0OOOO00OO += 1
            elif O0O0OO0O00OO0O0OO.delivery_status_id.code in O0000O000OOO00OO0:
                OOO000OOO00OOOO00 += 1
        O0OO00O0000OO0O00 = O0OOOOOOOOO00000O - O0O0000O0OOOO00OO - OOO000OOO00OOOO00
        OO0000OOO0O00OOO0 = round(O0O0000O0OOOO00OO / O0OOOOOOOOO00000O * 100, 1) if O0OOOOOOOOO00000O else 0
        OO000OOOOOOO0OOO0 = O00O00O000OOOOOOO - O000OOOOOOOOOO000
        OO00O00O0OO000O0O = round(OO000OOOOOOO0OOO0 / O000OOOOOOOOOO000 * 100, 1) if O000OOOOOOOOOO000 else 0
        O0O00O0O0OOOO0OO0 = len(set(O00O0O00000OO0000.mapped('carrier_id.id')))
        O0000O00OOO00O0O0 = {}
        for OOO0OOOO0O000O000 in O00O0O00000OO0000:
            OO00OOO00OO00OO0O = OOO0OOOO0O000O000.carrier_id.id
            if OO00OOO00OO00OO0O not in O0000O00OOO00O0O0:
                O0000O00OOO00O0O0[OO00OOO00OO00OO0O] = {'name': OOO0OOOO0O000O000.carrier_id.name, 'total': 0, 'completed': 0}
            O0000O00OOO00O0O0[OO00OOO00OO00OO0O]['total'] += 1
            OOO0O00OOO0O0O0OO = False
            if OOO0OOOO0O000O000.mapped_status_id:
                OOO0O00OOO0O0O0OO = OOO0OOOO0O000O000.mapped_status_id.code == 'delivered'
            else:
                OOO0O00OOO0O0O0OO = OOO0OOOO0O000O000.delivery_status_id.code in OO00O0O0OO0OOO0OO
            if OOO0O00OOO0O0O0OO:
                O0000O00OOO00O0O0[OO00OOO00OO00OO0O]['completed'] += 1
        O0O0000O000OO000O = []
        for OOO0O000OOOO000O0 in sorted(O0000O00OOO00O0O0.values(), key=lambda x: x['total'], reverse=True):
            OO000O00O0O00O000 = round(OOO0O000OOOO000O0['completed'] / OOO0O000OOOO000O0['total'] * 100, 1) if OOO0O000OOOO000O0['total'] else 0
            O0O0000O000OO000O.append({'name': OOO0O000OOOO000O0['name'], 'completed': OOO0O000OOOO000O0['completed'], 'total': OOO0O000OOOO000O0['total'], 'rate': OO000O00O0O00O000})
        return {'total_orders': O0OOOOOOOOO00000O, 'completed': O0O0000O0OOOO00OO, 'in_transit': O0OO00O0000OO0O00, 'cancelled': OOO000OOO00OOOO00, 'success_rate': OO0000OOO0O00OOO0, 'total_est_cost': O000OOOOOOOOOO000, 'total_real_cost': O00O00O000OOOOOOO, 'cost_diff': OO000OOOOOOO0OOO0, 'cost_diff_pct': OO00O00O0OO000O0O, 'total_cod': OOOO0O00O0O00000O, 'cod_orders': O00OOO0OO0OOO0OOO, 'carriers_used': O0O00O0O0OOOO0OO0, 'carrier_success_rates': O0O0000O000OO000O}

    @api.model
    def _get_carrier_breakdown(self, domain):
        O0OO00OO0OO0000O0 = self.env['carrier.ref.order']
        O0OO000O0O000OO00 = O0OO00OO0OO0000O0.search(domain)
        OOO0OOO0O0O00O0O0 = ['501', 'COMPLETED', '6']
        O0O0O00000OO0OOOO = {}
        for OO0O0O00O00OO0OO0 in O0OO000O0O000OO00:
            O0OO0OO0OOO0OOOOO = OO0O0O00O00OO0OO0.carrier_id.id
            if O0OO0OO0OOO0OOOOO not in O0O0O00000OO0OOOO:
                O0O0O00000OO0OOOO[O0OO0OO0OOO0OOOOO] = {'id': O0OO0OO0OOO0OOOOO, 'name': OO0O0O00O00OO0OO0.carrier_id.name, 'delivery_type': OO0O0O00O00OO0OO0.delivery_type, 'total_orders': 0, 'completed': 0, 'est_cost': 0, 'real_cost': 0, 'cod_orders': 0, 'cod_amount': 0, 'paid_amount': 0, 'unpaid_amount': 0}
            O0O0O00000OO0OOOO[O0OO0OO0OOO0OOOOO]['total_orders'] += 1
            O0O0O00000OO0OOOO[O0OO0OO0OOO0OOOOO]['est_cost'] += OO0O0O00O00OO0OO0.delivery_charge
            O0O0O00000OO0OOOO[O0OO0OO0OOO0OOOOO]['real_cost'] += OO0O0O00O00OO0OO0.real_delivery_charge
            if OO0O0O00O00OO0OO0.cash_on_delivery:
                O0O0O00000OO0OOOO[O0OO0OO0OOO0OOOOO]['cod_orders'] += 1
                O0O0O00000OO0OOOO[O0OO0OO0OOO0OOOOO]['cod_amount'] += OO0O0O00O00OO0OO0.cash_on_delivery_amount
            O000O0OO00OO0O000 = OO0O0O00O00OO0OO0.real_delivery_charge or OO0O0O00O00OO0OO0.delivery_charge
            if OO0O0O00O00OO0OO0.payment_status in ('paid', 'in_payment'):
                O0O0O00000OO0OOOO[O0OO0OO0OOO0OOOOO]['paid_amount'] += O000O0OO00OO0O000
            else:
                O0O0O00000OO0OOOO[O0OO0OO0OOO0OOOOO]['unpaid_amount'] += O000O0OO00OO0O000
            O00000OO00OOOOO0O = False
            if OO0O0O00O00OO0OO0.mapped_status_id:
                O00000OO00OOOOO0O = OO0O0O00O00OO0OO0.mapped_status_id.code == 'delivered'
            else:
                O00000OO00OOOOO0O = OO0O0O00O00OO0OO0.delivery_status_id.code in OOO0OOO0O0O00O0O0
            if O00000OO00OOOOO0O:
                O0O0O00000OO0OOOO[O0OO0OO0OOO0OOOOO]['completed'] += 1
        OO00OO0O0OO0O00OO = sorted(O0O0O00000OO0OOOO.values(), key=lambda x: x['total_orders'], reverse=True)
        for OOO00OOO0000O0O00 in OO00OO0O0OO0O00OO:
            OOO00OOO0000O0O00['avg_cost'] = round(OOO00OOO0000O0O00['real_cost'] / OOO00OOO0000O0O00['total_orders'], 0) if OOO00OOO0000O0O00['total_orders'] else 0
            OOO00OOO0000O0O00['success_rate'] = round(OOO00OOO0000O0O00['completed'] / OOO00OOO0000O0O00['total_orders'] * 100, 1) if OOO00OOO0000O0O00['total_orders'] else 0
        return OO00OO0O0OO0O00OO

    @api.model
    def _get_daily_orders(self, domain, date_from, date_to):
        OO0OO000OOOO00O00 = self.env['carrier.ref.order']
        O00OOOOO00OO00O00 = OO0OO000OOOO00O00.search(domain)
        O0OOO0OO0OO0OO00O = {}
        O00000O0OO00000O0 = date_from
        while O00000O0OO00000O0 <= date_to:
            O0OOO0OO0OO0OO00O[str(O00000O0OO00000O0)] = 0
            O00000O0OO00000O0 += timedelta(days=1)
        for OOO0O0OO0OOOOOOOO in O00OOOOO00OO00O00:
            O00O0O00OO00OOOO0 = str(OOO0O0OO0OOOOOOOO.create_date.date())
            if O00O0O00OO00OOOO0 in O0OOO0OO0OO0OO00O:
                O0OOO0OO0OO0OO00O[O00O0O00OO00OOOO0] += 1
        return [{'date': k, 'count': v} for k, v in sorted(O0OOO0OO0OO0OO00O.items())]

    @api.model
    def _get_status_distribution(self, domain):
        O0OOO0O0OO0O000O0 = self.env['carrier.ref.order']
        OOOO0OO0000OO000O = O0OOO0O0OO0O000O0.search(domain)
        OO00O0O0O00O0OO00 = {}
        for OOO0O0O00O0000OOO in OOOO0OO0000OO000O:
            if OOO0O0O00O0000OOO.mapped_status_id:
                OO0OOO0O00O00OOO0 = OOO0O0O00O0000OOO.mapped_status_id.name
            else:
                OO0OOO0O00O00OOO0 = OOO0O0O00O0000OOO.delivery_status_id.name or 'Unknown'
            if OO0OOO0O00O00OOO0 not in OO00O0O0O00O0OO00:
                OO00O0O0O00O0OO00[OO0OOO0O00O00OOO0] = 0
            OO00O0O0O00O0OO00[OO0OOO0O00O00OOO0] += 1
        return [{'status': k, 'count': v} for k, v in sorted(OO00O0O0O00O0OO00.items(), key=lambda x: x[1], reverse=True)]

    @api.model
    def _get_cost_comparison(self, domain):
        OO000O00O00OOOOO0 = self.env['carrier.ref.order']
        OOOOO00O00O0O00O0 = OO000O00O00OOOOO0.search(domain)
        OOOOOOOOO0O0O0OO0 = {}
        for O0000O00OO00OOOOO in OOOOO00O00O0O00O0:
            O0O0OOOO0O00O00O0 = O0000O00OO00OOOOO.carrier_id.name
            if O0O0OOOO0O00O00O0 not in OOOOOOOOO0O0O0OO0:
                OOOOOOOOO0O0O0OO0[O0O0OOOO0O00O00O0] = {'carrier': O0O0OOOO0O00O00O0, 'estimated': 0, 'actual': 0, 'count': 0}
            OOOOOOOOO0O0O0OO0[O0O0OOOO0O00O00O0]['estimated'] += O0000O00OO00OOOOO.delivery_charge
            OOOOOOOOO0O0O0OO0[O0O0OOOO0O00O00O0]['actual'] += O0000O00OO00OOOOO.real_delivery_charge
            OOOOOOOOO0O0O0OO0[O0O0OOOO0O00O00O0]['count'] += 1
        OO00OO0000O0O0OO0 = list(OOOOOOOOO0O0O0OO0.values())
        for OO0OO0O0OOOO0OO0O in OO00OO0000O0O0OO0:
            OO0OO0O0OOOO0OO0O['diff'] = OO0OO0O0OOOO0OO0O['actual'] - OO0OO0O0OOOO0OO0O['estimated']
            OO0OO0O0OOOO0OO0O['diff_pct'] = round(OO0OO0O0OOOO0OO0O['diff'] / OO0OO0O0OOOO0OO0O['estimated'] * 100, 1) if OO0OO0O0OOOO0OO0O['estimated'] else 0
        return sorted(OO00OO0000O0O0OO0, key=lambda x: x['count'], reverse=True)

    @api.model
    def _get_cod_summary(self, domain):
        O000O0OOOOOO000OO = self.env['carrier.ref.order']
        O0O0O0O0O0OO0O0O0 = domain + [('cash_on_delivery', '=', True)]
        O0000O000000000OO = O000O0OOOOOO000OO.search(O0O0O0O0O0OO0O0O0)
        OO0OO0OOO0O0000O0 = {}
        for O0O0000OOO00O000O in O0000O000000000OO:
            OO00O00OOOOOO0OOO = O0O0000OOO00O000O.carrier_id.name
            if OO00O00OOOOOO0OOO not in OO0OO0OOO0O0000O0:
                OO0OO0OOO0O0000O0[OO00O00OOOOOO0OOO] = {'carrier': OO00O00OOOOOO0OOO, 'orders': 0, 'amount': 0}
            OO0OO0OOO0O0000O0[OO00O00OOOOOO0OOO]['orders'] += 1
            OO0OO0OOO0O0000O0[OO00O00OOOOOO0OOO]['amount'] += O0O0000OOO00O000O.cash_on_delivery_amount
        return sorted(OO0OO0OOO0O0000O0.values(), key=lambda x: x['amount'], reverse=True)

    @api.model
    def _get_carriers_list(self):
        OOO0OOOO0OOO00OO0 = self.env['delivery.carrier'].search([('delivery_type', 'not in', ['fixed', 'base_on_rule'])])
        return [{'id': c.id, 'name': c.name, 'delivery_type': c.delivery_type} for c in OOO0OOOO0OOO00OO0]

    @api.model
    def _get_standard_status_cards(self, domain):
        OO00O0OOO00OOOOO0 = self.env['carrier.ref.order']
        O0000O0O0OO0O0O0O = OO00O0OOO00OOOOO0.search(domain)
        O0000O0OOOOOO00O0 = self.env['delivery.standard.status']
        OO00OO000OO00OO00 = O0000O0OOOOOO00O0.search([('show_on_dashboard', '=', True)], order='sequence')
        OO00OOO0OO00O000O = {}
        for OOOOOO00OO0O00OOO in O0000O0O0OO0O0O0O:
            OO000OOO00OOO00O0 = OOOOOO00OO0O00OOO.mapped_status or '_unmapped'
            OO00OOO0OO00O000O[OO000OOO00OOO00O0] = OO00OOO0OO00O000O.get(OO000OOO00OOO00O0, 0) + 1
        OO00OO0O0OOOO0OOO = []
        for O0O0O00O0OO0O00OO in OO00OO000OO00OO00:
            OO00OO0O0OOOO0OOO.append({'code': O0O0O00O0OO0O00OO.code, 'name': O0O0O00O0OO0O00OO.name, 'count': OO00OOO0OO00O000O.get(O0O0O00O0OO0O00OO.code, 0), 'color': O0O0O00O0OO0O00OO.color or '#6c757d'})
        return OO00OO0O0OOOO0OOO

    @api.model
    def _get_webhook_stats(self, domain, date_from, date_to):
        OO000O00OOO00O0OO = self.env['delivery.webhook.log']
        O0000000O0O000O00 = OO000O00OOO00O0OO.search(domain)
        OO00OO0000OO0OOO0 = len(O0000000O0O000O00)
        O00OOO0OO0OOO0O0O = len(O0000000O0O000O00.filtered(lambda l: l.response_status == 'success'))
        O00O0000OOO000000 = len(O0000000O0O000O00.filtered(lambda l: l.response_status == 'error'))
        OO00O000O0OOO0000 = len(O0000000O0O000O00.filtered(lambda l: l.response_status == 'ignored'))
        O0OO0000OO0OO000O = [l.processing_time_ms for l in O0000000O0O000O00 if l.processing_time_ms]
        O00O000O00O0OOO00 = round(sum(O0OO0000OO0OO000O) / len(O0OO0000OO0OO000O)) if O0OO0000OO0OO000O else 0
        OO00OOO0O000OO00O = max(O0OO0000OO0OO000O) if O0OO0000OO0OO000O else 0
        OO00OO000O0OO0O00 = round(O00OOO0OO0OOO0O0O / OO00OO0000OO0OOO0 * 100, 1) if OO00OO0000OO0OOO0 else 0
        OO0O00O0O0000O0O0 = defaultdict(lambda: {'total': 0, 'success': 0, 'error': 0, 'ignored': 0, 'avg_time': 0, 'times': []})
        for O000O0O00O0O00O0O in O0000000O0O000O00:
            O0O0OO000OO0O000O = O000O0O00O0O00O0O.carrier_type or 'unknown'
            OO0O00O0O0000O0O0[O0O0OO000OO0O000O]['total'] += 1
            if O000O0O00O0O00O0O.response_status == 'success':
                OO0O00O0O0000O0O0[O0O0OO000OO0O000O]['success'] += 1
            elif O000O0O00O0O00O0O.response_status == 'error':
                OO0O00O0O0000O0O0[O0O0OO000OO0O000O]['error'] += 1
            else:
                OO0O00O0O0000O0O0[O0O0OO000OO0O000O]['ignored'] += 1
            if O000O0O00O0O00O0O.processing_time_ms:
                OO0O00O0O0000O0O0[O0O0OO000OO0O000O]['times'].append(O000O0O00O0O00O0O.processing_time_ms)
        OO0OOOO000OOO0O0O = []
        for OOO00OO000O0OO0OO, OO000O0OOO0O0O000 in sorted(OO0O00O0O0000O0O0.items(), key=lambda x: x[1]['total'], reverse=True):
            OOOO0O00O0O0OO0O0 = round(sum(OO000O0OOO0O0O000['times']) / len(OO000O0OOO0O0O000['times'])) if OO000O0OOO0O0O000['times'] else 0
            OO0OOOO000OOO0O0O.append({'carrier_type': OOO00OO000O0OO0OO, 'total': OO000O0OOO0O0O000['total'], 'success': OO000O0OOO0O0O000['success'], 'error': OO000O0OOO0O0O000['error'], 'ignored': OO000O0OOO0O0O000['ignored'], 'avg_time': OOOO0O00O0O0OO0O0, 'success_rate': round(OO000O0OOO0O0O000['success'] / OO000O0OOO0O0O000['total'] * 100, 1) if OO000O0OOO0O0O000['total'] else 0})
        OOOOOO000O000O0OO = {}
        OO0OOO00O000O000O = date_from
        while OO0OOO00O000O000O <= date_to:
            OOOOOO000O000O0OO[str(OO0OOO00O000O000O)] = {'success': 0, 'error': 0, 'ignored': 0}
            OO0OOO00O000O000O += timedelta(days=1)
        for O000O0O00O0O00O0O in O0000000O0O000O00:
            OO00OO0OO000OO0O0 = str(O000O0O00O0O00O0O.create_date.date())
            if OO00OO0OO000OO0O0 in OOOOOO000O000O0OO:
                O0O0O0OOO000OOO0O = O000O0O00O0O00O0O.response_status or 'success'
                if O0O0O0OOO000OOO0O in OOOOOO000O000O0OO[OO00OO0OO000OO0O0]:
                    OOOOOO000O000O0OO[OO00OO0OO000OO0O0][O0O0O0OOO000OOO0O] += 1
        OOO0000000OOO0OO0 = [{'date': k, 'success': v['success'], 'error': v['error'], 'ignored': v['ignored'], 'total': v['success'] + v['error'] + v['ignored']} for k, v in sorted(OOOOOO000O000O0OO.items())]
        OOO00OO0000000OO0 = OO000O00OOO00O0OO.search(domain + [('response_status', '=', 'error')], order='create_date desc', limit=10)
        O000OOO0000O00O00 = [{'id': O000O0O00O0O00O0O.id, 'date': fields.Datetime.to_string(O000O0O00O0O00O0O.create_date), 'carrier_type': O000O0O00O0O00O0O.carrier_type or '', 'tracking_ref': O000O0O00O0O00O0O.tracking_ref or '', 'error_message': O000O0O00O0O00O0O.error_message or '', 'processing_time_ms': O000O0O00O0O00O0O.processing_time_ms} for O000O0O00O0O00O0O in OOO00OO0000000OO0]
        return {'total': OO00OO0000OO0OOO0, 'success': O00OOO0OO0OOO0O0O, 'error': O00O0000OOO000000, 'ignored': OO00O000O0OOO0000, 'success_rate': OO00OO000O0OO0O00, 'avg_processing_time': O00O000O00O0OOO00, 'max_processing_time': OO00OOO0O000OO00O, 'carrier_breakdown': OO0OOOO000OOO0O0O, 'daily_data': OOO0000000OOO0OO0, 'recent_errors': O000OOO0000O00O00}

    @api.model
    def _get_performance_analytics(self, domain, date_from, date_to):
        return {'cost_efficiency': self._get_cost_efficiency(domain), 'delivery_speed': self._get_delivery_speed(domain), 'failure_analysis': self._get_failure_analysis(domain, date_from, date_to), 'geographic_performance': self._get_geographic_performance(domain), 'carrier_scorecard': self._get_carrier_scorecard(domain)}

    @api.model
    def _get_cost_efficiency(self, domain):
        OOOO0O00OO000OOOO = self.env['carrier.ref.order']
        OO00000000O0O0000 = OOOO0O00OO000OOOO.search(domain)
        OO00O00O0O00OOO0O = {}
        for OOO00OO00O000O000 in OO00000000O0O0000:
            O00OOO0OOOOOO0O0O = OOO00OO00O000O000.carrier_id.id
            if O00OOO0OOOOOO0O0O not in OO00O00O0O00OOO0O:
                OO00O00O0O00OOO0O[O00OOO0OOOOOO0O0O] = {'carrier_id': O00OOO0OOOOOO0O0O, 'carrier_name': OOO00OO00O000O000.carrier_id.name, 'delivery_type': OOO00OO00O000O000.delivery_type, 'total_orders': 0, 'delivered_count': 0, 'failed_count': 0, 'total_est_cost': 0, 'total_real_cost': 0, 'cost_overrun_count': 0, 'cost_overrun_total': 0}
            O0O0O0O0000000OOO = OO00O00O0O00OOO0O[O00OOO0OOOOOO0O0O]
            O0O0O0O0000000OOO['total_orders'] += 1
            O0O0O0O0000000OOO['total_est_cost'] += OOO00OO00O000O000.delivery_charge or 0
            O0O0O0O0000000OOO['total_real_cost'] += OOO00OO00O000O000.real_delivery_charge or 0
            if OOO00OO00O000O000.real_delivery_charge and OOO00OO00O000O000.delivery_charge:
                O000OOOOO0OOO0000 = OOO00OO00O000O000.real_delivery_charge - OOO00OO00O000O000.delivery_charge
                if O000OOOOO0OOO0000 > 0:
                    O0O0O0O0000000OOO['cost_overrun_count'] += 1
                    O0O0O0O0000000OOO['cost_overrun_total'] += O000OOOOO0OOO0000
            if OOO00OO00O000O000.mapped_status_id:
                if OOO00OO00O000O000.mapped_status_id.code == 'delivered':
                    O0O0O0O0000000OOO['delivered_count'] += 1
                elif OOO00OO00O000O000.mapped_status_id.code in ('failed', 'cancelled', 'returned'):
                    O0O0O0O0000000OOO['failed_count'] += 1
            else:
                OO000OOO000OOOOOO = ['501', 'COMPLETED', '6']
                O000OOO00O0O000OO = ['503', 'CANCELED', 'REJECTED', 'EXPIRED', '-1', 'CANCELLED']
                O0OO0OO00OO0O00O0 = OOO00OO00O000O000.delivery_status_id.code or ''
                if O0OO0OO00OO0O00O0 in OO000OOO000OOOOOO:
                    O0O0O0O0000000OOO['delivered_count'] += 1
                elif O0OO0OO00OO0O00O0 in O000OOO00O0O000OO:
                    O0O0O0O0000000OOO['failed_count'] += 1
        O0O00O0O0O0OO0OO0 = []
        for O0O0O0O0000000OOO in sorted(OO00O00O0O00OOO0O.values(), key=lambda x: x['total_orders'], reverse=True):
            O00000O00OO0O000O = O0O0O0O0000000OOO['delivered_count']
            O0O000O000OO0O0OO = round(O0O0O0O0000000OOO['total_real_cost'] / O0O0O0O0000000OOO['total_orders'], 0) if O0O0O0O0000000OOO['total_orders'] else 0
            O0O00OOO00O0OOOO0 = round(O0O0O0O0000000OOO['total_real_cost'] / O00000O00OO0O000O, 0) if O00000O00OO0O000O else 0
            O0O0OOOOOO0OOOO00 = round(O0O0O0O0000000OOO['cost_overrun_total'] / O0O0O0O0000000OOO['total_est_cost'] * 100, 1) if O0O0O0O0000000OOO['total_est_cost'] else 0
            O00O000O000000OO0 = round(O00000O00OO0O000O / O0O0O0O0000000OOO['total_orders'] * 100, 1) if O0O0O0O0000000OOO['total_orders'] else 0
            O0O00O0O0O0OO0OO0.append({'carrier_id': O0O0O0O0000000OOO['carrier_id'], 'carrier_name': O0O0O0O0000000OOO['carrier_name'], 'delivery_type': O0O0O0O0000000OOO['delivery_type'], 'total_orders': O0O0O0O0000000OOO['total_orders'], 'delivered': O00000O00OO0O000O, 'failed': O0O0O0O0000000OOO['failed_count'], 'success_rate': O00O000O000000OO0, 'avg_cost_per_shipment': O0O000O000OO0O0OO, 'true_cost_per_delivery': O0O00OOO00O0OOOO0, 'total_est_cost': O0O0O0O0000000OOO['total_est_cost'], 'total_real_cost': O0O0O0O0000000OOO['total_real_cost'], 'cost_overrun_count': O0O0O0O0000000OOO['cost_overrun_count'], 'cost_overrun_pct': O0O0OOOOOO0OOOO00, 'waste_cost': O0O0O0O0000000OOO['total_real_cost'] - O0O000O000OO0O0OO * O00000O00OO0O000O if O00000O00OO0O000O else 0})
        return O0O00O0O0O0OO0OO0

    @api.model
    def _get_delivery_speed(self, domain):
        O0OO0OOOO000000OO = self.env['carrier.ref.order']
        OO00O00OO0O0000O0 = domain + [('mapped_status', '=', 'delivered')]
        O00OO0O00OO000O0O = O0OO0OOOO000000OO.search(OO00O00OO0O0000O0)
        OO0O0000O0O000OOO = {}
        for O0O0O000OOO0O0O0O in O00OO0O00OO000O0O:
            OOO000OOO00O0O000 = O0O0O000OOO0O0O0O.carrier_id.id
            if OOO000OOO00O0O000 not in OO0O0000O0O000OOO:
                OO0O0000O0O000OOO[OOO000OOO00O0O000] = {'carrier_name': O0O0O000OOO0O0O0O.carrier_id.name, 'delivery_type': O0O0O000OOO0O0O0O.delivery_type, 'durations': []}
            if O0O0O000OOO0O0O0O.create_date and O0O0O000OOO0O0O0O.write_date:
                OO0O00OOOOOO00000 = (O0O0O000OOO0O0O0O.write_date - O0O0O000OOO0O0O0O.create_date).total_seconds() / 3600
                if OO0O00OOOOOO00000 > 0:
                    OO0O0000O0O000OOO[OOO000OOO00O0O000]['durations'].append(OO0O00OOOOOO00000)
        OOOOOO0OOOO00000O = []
        for OOO000OOO00O0O000, OOOO00OOOO00O0000 in OO0O0000O0O000OOO.items():
            OO00O0O0O000OO000 = OOOO00OOOO00O0000['durations']
            if not OO00O0O0O000OO000:
                continue
            O0O00OOO0O0O00000 = round(sum(OO00O0O0O000OO000) / len(OO00O0O0O000OO000), 1)
            OO0O0000O0OOO0OO0 = round(min(OO00O0O0O000OO000), 1)
            OO00OOOO0O000O0OO = round(max(OO00O0O0O000OO000), 1)
            OO0OO000OO0OO0OOO = sorted(OO00O0O0O000OO000)
            O00O00OOOO0OO0OOO = len(OO0OO000OO0OO0OOO) // 2
            O0OO00O00O00O00O0 = round((OO0OO000OO0OO0OOO[O00O00OOOO0OO0OOO] + OO0OO000OO0OO0OOO[O00O00OOOO0OO0OOO - 1]) / 2 if len(OO0OO000OO0OO0OOO) % 2 == 0 else OO0OO000OO0OO0OOO[O00O00OOOO0OO0OOO], 1)
            OO0O0OO000OOOOO00 = len([x for x in OO00O0O0O000OO000 if x <= 48])
            O00O00000O0OOOO0O = round(OO0O0OO000OOOOO00 / len(OO00O0O0O000OO000) * 100, 1)
            OOOOOO0OOOO00000O.append({'carrier_name': OOOO00OOOO00O0000['carrier_name'], 'delivery_type': OOOO00OOOO00O0000['delivery_type'], 'total_delivered': len(OO00O0O0O000OO000), 'avg_hours': O0O00OOO0O0O00000, 'median_hours': O0OO00O00O00O00O0, 'min_hours': OO0O0000O0OOO0OO0, 'max_hours': OO00OOOO0O000O0OO, 'sla_48h_pct': O00O00000O0OOOO0O})
        return sorted(OOOOOO0OOOO00000O, key=lambda x: x['avg_hours'])

    @api.model
    def _get_failure_analysis(self, domain, date_from, date_to):
        O0O00000O0O000OOO = self.env['carrier.ref.order']
        OO0OOOO0O0OO00OOO = domain + [('mapped_status', 'in', ['failed', 'cancelled', 'returned'])]
        O000OO0OO0O000OO0 = O0O00000O0O000OOO.search(OO0OOOO0O0OO00OOO)
        OOOOO0OO00O000OO0 = defaultdict(lambda: defaultdict(int))
        O0OOO00OOO0O00OOO = defaultdict(lambda: defaultdict(int))
        for O000OO00OOOOO0O0O in O000OO0OO0O000OO0:
            OOO0OO00OO0OO000O = O000OO00OOOOO0O0O.create_date.strftime('%Y-W%W')
            O0O000OO000OOOO0O = O000OO00OOOOO0O0O.carrier_id.name
            OOOOO0OO00O000OO0[OOO0OO00OO0OO000O][O0O000OO000OOOO0O] += 1
            O0OO000O000OOOO0O = O000OO00OOOOO0O0O.mapped_status_id.name if O000OO00OOOOO0O0O.mapped_status_id else 'Unknown'
            O0OOO00OOO0O00OOO[O0O000OO000OOOO0O][O0OO000O000OOOO0O] += 1
        OO0OO0O00O00O0O0O = sorted(OOOOO0OO00O000OO0.keys())
        OO0OO0OO00OO0O0OO = set()
        for OOO0OOOOO0OO0O00O in OOOOO0OO00O000OO0.values():
            OO0OO0OO00OO0O0OO.update(OOO0OOOOO0OO0O00O.keys())
        OO0OO0OO00OO0O0OO = sorted(OO0OO0OO00OO0O0OO)
        O0OO0O00O0OOOOOOO = []
        for OOO0OO00OO0OO000O in OO0OO0O00O00O0O0O:
            O0OOO00O000O0O00O = {'week': OOO0OO00OO0OO000O}
            for O00O0000O00O00OO0 in OO0OO0OO00OO0O0OO:
                O0OOO00O000O0O00O[O00O0000O00O00OO0] = OOOOO0OO00O000OO0[OOO0OO00OO0OO000O].get(O00O0000O00O00OO0, 0)
            O0OO0O00O0OOOOOOO.append(O0OOO00O000O0O00O)
        O000O00O0O0O0OO0O = []
        for O00O0000O00O00OO0, OOO00OOOO0O000O00 in sorted(O0OOO00OOO0O00OOO.items()):
            OO0OO00OO00O0OO00 = sum(OOO00OOOO0O000O00.values())
            OO000O0OOOO0OO00O = []
            for O0O0O00OOOOOOO00O, O0O0O000O00O00OOO in sorted(OOO00OOOO0O000O00.items(), key=lambda x: x[1], reverse=True):
                OO000O0OOOO0OO00O.append({'reason': O0O0O00OOOOOOO00O, 'count': O0O0O000O00O00OOO, 'pct': round(O0O0O000O00O00OOO / OO0OO00OO00O0OO00 * 100, 1) if OO0OO00OO00O0OO00 else 0})
            O000O00O0O0O0OO0O.append({'carrier': O00O0000O00O00OO0, 'total_failures': OO0OO00OO00O0OO00, 'reasons': OO000O0OOOO0OO00O})
        return {'weekly_trend': O0OO0O00O0OOOOOOO, 'carriers': OO0OO0OO00OO0O0OO, 'failure_reasons': sorted(O000O00O0O0O0OO0O, key=lambda x: x['total_failures'], reverse=True), 'total_failures': len(O000OO0OO0O000OO0)}

    @api.model
    def _get_geographic_performance(self, domain):
        O0000O0O0O0O0O000 = self.env['carrier.ref.order']
        OO00OOO0OO00OO000 = O0000O0O0O0O0O000.search(domain)
        OO0OOO000O0O0O0OO = {}
        for OOO00O0OOO000O0O0 in OO00OOO0OO00OO000:
            OOOO0OO0OOOO0O000 = OOO00O0OOO000O0O0.picking_id.partner_id if OOO00O0OOO000O0O0.picking_id else None
            if not OOOO0OO0OOOO0O000:
                continue
            OOO0O0O000O0000OO = OOOO0OO0OOOO0O000.state_id.name if OOOO0OO0OOOO0O000.state_id else 'Unknown'
            O00OO00OO0000OOO0 = OOO00O0OOO000O0O0.carrier_id.name
            O0OO0O000O00000OO = (OOO0O0O000O0000OO, O00OO00OO0000OOO0)
            if O0OO0O000O00000OO not in OO0OOO000O0O0O0OO:
                OO0OOO000O0O0O0OO[O0OO0O000O00000OO] = {'province': OOO0O0O000O0000OO, 'carrier': O00OO00OO0000OOO0, 'total': 0, 'delivered': 0, 'failed': 0, 'total_cost': 0}
            OOOOO0OO00OOO000O = OO0OOO000O0O0O0OO[O0OO0O000O00000OO]
            OOOOO0OO00OOO000O['total'] += 1
            OOOOO0OO00OOO000O['total_cost'] += OOO00O0OOO000O0O0.real_delivery_charge or OOO00O0OOO000O0O0.delivery_charge or 0
            if OOO00O0OOO000O0O0.mapped_status_id:
                if OOO00O0OOO000O0O0.mapped_status_id.code == 'delivered':
                    OOOOO0OO00OOO000O['delivered'] += 1
                elif OOO00O0OOO000O0O0.mapped_status_id.code in ('failed', 'cancelled', 'returned'):
                    OOOOO0OO00OOO000O['failed'] += 1
        O00000O000OOOO0OO = []
        for OOOOO0OO00OOO000O in OO0OOO000O0O0O0OO.values():
            OOOOO0OO00OOO000O['success_rate'] = round(OOOOO0OO00OOO000O['delivered'] / OOOOO0OO00OOO000O['total'] * 100, 1) if OOOOO0OO00OOO000O['total'] else 0
            OOOOO0OO00OOO000O['avg_cost'] = round(OOOOO0OO00OOO000O['total_cost'] / OOOOO0OO00OOO000O['total'], 0) if OOOOO0OO00OOO000O['total'] else 0
            O00000O000OOOO0OO.append(OOOOO0OO00OOO000O)
        return sorted(O00000O000OOOO0OO, key=lambda x: (-x['total'], x['province']))

    @api.model
    def _get_carrier_scorecard(self, domain):
        OO0O00O00O0OO0O00 = self._get_cost_efficiency(domain)
        O0OO0O00O0000O000 = self._get_delivery_speed(domain)
        OO000000O0OO0O000 = {d['carrier_name']: d for d in O0OO0O00O0000O000}
        OO0OO0O0OO00O0OOO = []
        for OOO00OO00OOOO000O in OO0O00O00O0OO0O00:
            OO0OO0OO0000OOOO0 = OOO00OO00OOOO000O['carrier_name']
            OO0O0O00O00O0000O = OO000000O0OO0O000.get(OO0OO0OO0000OOOO0, {})
            OOOOOOO0O00O000O0 = min(OOO00OO00OOOO000O['success_rate'], 100)
            O00OO0000O0O0000O = OO0O0O00O00O0000O.get('avg_hours', 168)
            O0OOOO00OOOOOOOOO = max(0, min(100, 100 - (O00OO0000O0O0000O - 24) / (168 - 24) * 100))
            O0OOO0O0O00O000O0 = OOO00OO00OOOO000O['cost_overrun_pct']
            OO0O0OOOOO000O0OO = max(0, min(100, 100 - O0OOO0O0O00O000O0 / 20 * 100))
            OOO0OO00O0O00O00O = 0
            if OOO00OO00OOOO000O['total_orders']:
                OOO0OO00O0O00O00O = round((OOO00OO00OOOO000O['total_orders'] - OOO00OO00OOOO000O['cost_overrun_count']) / OOO00OO00OOOO000O['total_orders'] * 100, 1)
            OO0OO000OO00OOO00 = round(0.35 * OOOOOOO0O00O000O0 + 0.25 * O0OOOO00OOOOOOOOO + 0.25 * OO0O0OOOOO000O0OO + 0.15 * OOO0OO00O0O00O00O, 1)
            OO0OO0O0OO00O0OOO.append({'carrier_name': OO0OO0OO0000OOOO0, 'delivery_type': OOO00OO00OOOO000O['delivery_type'], 'total_orders': OOO00OO00OOOO000O['total_orders'], 'success_score': round(OOOOOOO0O00O000O0, 1), 'speed_score': round(O0OOOO00OOOOOOOOO, 1), 'cost_score': round(OO0O0OOOOO000O0OO, 1), 'reliability_score': round(OOO0OO00O0O00O00O, 1), 'final_score': OO0OO000OO00OOO00, 'success_rate': OOO00OO00OOOO000O['success_rate'], 'avg_hours': OO0O0O00O00O0000O.get('avg_hours', 0), 'true_cost': OOO00OO00OOOO000O['true_cost_per_delivery'], 'overrun_pct': OOO00OO00OOOO000O['cost_overrun_pct']})
        return sorted(OO0OO0O0OO00O0OOO, key=lambda x: x['final_score'], reverse=True)

    def init(self):
        pass