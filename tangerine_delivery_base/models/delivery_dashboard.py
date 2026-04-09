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
        """Main method to get all dashboard KPI data."""
        today = date.today()
        if not date_from:
            date_from = today.replace(day=1)
        else:
            date_from = fields.Date.from_string(date_from)
        if not date_to:
            date_to = today
        else:
            date_to = fields.Date.from_string(date_to)

        domain = [
            ('create_date', '>=', fields.Datetime.to_string(date_from)),
            ('create_date', '<=', fields.Datetime.to_string(date_to + timedelta(days=1))),
        ]
        if carrier_id:
            domain.append(('carrier_id', '=', carrier_id))

        # Webhook domain (carrier_id filter uses carrier_type or carrier_id)
        webhook_domain = [
            ('create_date', '>=', fields.Datetime.to_string(date_from)),
            ('create_date', '<=', fields.Datetime.to_string(date_to + timedelta(days=1))),
        ]
        if carrier_id:
            webhook_domain.append(('carrier_id', '=', carrier_id))

        result = {
            'currency_symbol': self.env.company.currency_id.symbol or '',
            'currency_code': self.env.company.currency_id.name or 'VND',
            'currency_position': self.env.company.currency_id.position or 'after',
            'kpi': self._get_kpi_data(domain),
            'carrier_breakdown': self._get_carrier_breakdown(domain),
            'daily_orders': self._get_daily_orders(domain, date_from, date_to),
            'status_distribution': self._get_status_distribution(domain),
            'cost_comparison': self._get_cost_comparison(domain),
            'cod_summary': self._get_cod_summary(domain),
            'carriers': self._get_carriers_list(),
            'webhook_stats': self._get_webhook_stats(webhook_domain, date_from, date_to),
            'performance': self._get_performance_analytics(domain, date_from, date_to),
            'standard_status_cards': self._get_standard_status_cards(domain),
        }

        return result

    @api.model
    def _get_kpi_data(self, domain):
        """Get top-level KPI cards data."""
        RefOrder = self.env['carrier.ref.order']
        orders = RefOrder.search(domain)
        total = len(orders)
        total_est_cost = sum(orders.mapped('delivery_charge'))
        total_real_cost = sum(orders.mapped('real_delivery_charge'))
        total_cod = sum(orders.filtered('cash_on_delivery').mapped('cash_on_delivery_amount'))
        cod_orders = len(orders.filtered('cash_on_delivery'))

        # Use mapped standard status if available, otherwise fallback to code comparison
        completed_codes = ['501', 'COMPLETED', '6']
        cancelled_codes = ['503', 'CANCELED', 'REJECTED', 'EXPIRED', '-1', 'CANCELLED']
        completed = 0
        cancelled = 0
        for o in orders:
            if o.mapped_status_id:
                if o.mapped_status_id.code == 'delivered':
                    completed += 1
                elif o.mapped_status_id.code in ('cancelled', 'failed'):
                    cancelled += 1
            else:
                if o.delivery_status_id.code in completed_codes:
                    completed += 1
                elif o.delivery_status_id.code in cancelled_codes:
                    cancelled += 1

        in_transit = total - completed - cancelled
        success_rate = round((completed / total) * 100, 1) if total else 0
        cost_diff = total_real_cost - total_est_cost
        cost_diff_pct = round((cost_diff / total_est_cost) * 100, 1) if total_est_cost else 0

        # Unique carriers used
        carriers_used = len(set(orders.mapped('carrier_id.id')))

        # Per-carrier success rates
        carrier_success = {}
        for order in orders:
            cid = order.carrier_id.id
            if cid not in carrier_success:
                carrier_success[cid] = {
                    'name': order.carrier_id.name,
                    'total': 0,
                    'completed': 0,
                }
            carrier_success[cid]['total'] += 1
            is_completed = False
            if order.mapped_status_id:
                is_completed = order.mapped_status_id.code == 'delivered'
            else:
                is_completed = order.delivery_status_id.code in completed_codes
            if is_completed:
                carrier_success[cid]['completed'] += 1

        carrier_success_rates = []
        for data in sorted(carrier_success.values(), key=lambda x: x['total'], reverse=True):
            rate = round((data['completed'] / data['total']) * 100, 1) if data['total'] else 0
            carrier_success_rates.append({
                'name': data['name'],
                'completed': data['completed'],
                'total': data['total'],
                'rate': rate,
            })

        return {
            'total_orders': total,
            'completed': completed,
            'in_transit': in_transit,
            'cancelled': cancelled,
            'success_rate': success_rate,
            'total_est_cost': total_est_cost,
            'total_real_cost': total_real_cost,
            'cost_diff': cost_diff,
            'cost_diff_pct': cost_diff_pct,
            'total_cod': total_cod,
            'cod_orders': cod_orders,
            'carriers_used': carriers_used,
            'carrier_success_rates': carrier_success_rates,
        }

    @api.model
    def _get_carrier_breakdown(self, domain):
        """Get order count and cost per carrier with payment breakdown."""
        RefOrder = self.env['carrier.ref.order']
        orders = RefOrder.search(domain)
        completed_codes = ['501', 'COMPLETED', '6']
        carrier_data = {}
        for order in orders:
            cid = order.carrier_id.id
            if cid not in carrier_data:
                carrier_data[cid] = {
                    'id': cid,
                    'name': order.carrier_id.name,
                    'delivery_type': order.delivery_type,
                    'total_orders': 0,
                    'completed': 0,
                    'est_cost': 0,
                    'real_cost': 0,
                    'cod_orders': 0,
                    'cod_amount': 0,
                    'paid_amount': 0,
                    'unpaid_amount': 0,
                }
            carrier_data[cid]['total_orders'] += 1
            carrier_data[cid]['est_cost'] += order.delivery_charge
            carrier_data[cid]['real_cost'] += order.real_delivery_charge
            if order.cash_on_delivery:
                carrier_data[cid]['cod_orders'] += 1
                carrier_data[cid]['cod_amount'] += order.cash_on_delivery_amount
            # Payment tracking
            cost = order.real_delivery_charge or order.delivery_charge
            if order.payment_status in ('paid', 'in_payment'):
                carrier_data[cid]['paid_amount'] += cost
            else:
                carrier_data[cid]['unpaid_amount'] += cost
            # Success tracking
            is_completed = False
            if order.mapped_status_id:
                is_completed = order.mapped_status_id.code == 'delivered'
            else:
                is_completed = order.delivery_status_id.code in completed_codes
            if is_completed:
                carrier_data[cid]['completed'] += 1

        result = sorted(carrier_data.values(), key=lambda x: x['total_orders'], reverse=True)
        for item in result:
            item['avg_cost'] = round(item['real_cost'] / item['total_orders'], 0) if item['total_orders'] else 0
            item['success_rate'] = round((item['completed'] / item['total_orders']) * 100, 1) if item['total_orders'] else 0
        return result

    @api.model
    def _get_daily_orders(self, domain, date_from, date_to):
        """Get daily order counts for the chart."""
        RefOrder = self.env['carrier.ref.order']
        orders = RefOrder.search(domain)
        daily = {}
        current = date_from
        while current <= date_to:
            daily[str(current)] = 0
            current += timedelta(days=1)

        for order in orders:
            day_str = str(order.create_date.date())
            if day_str in daily:
                daily[day_str] += 1

        return [{'date': k, 'count': v} for k, v in sorted(daily.items())]

    @api.model
    def _get_status_distribution(self, domain):
        """Get order count per delivery status.
        Uses mapped standard status when available for unified grouping."""
        RefOrder = self.env['carrier.ref.order']
        orders = RefOrder.search(domain)
        status_data = {}
        for order in orders:
            if order.mapped_status_id:
                status_name = order.mapped_status_id.name
            else:
                status_name = order.delivery_status_id.name or 'Unknown'
            if status_name not in status_data:
                status_data[status_name] = 0
            status_data[status_name] += 1
        return [{'status': k, 'count': v} for k, v in
                sorted(status_data.items(), key=lambda x: x[1], reverse=True)]

    @api.model
    def _get_cost_comparison(self, domain):
        """Compare estimated vs real costs per carrier."""
        RefOrder = self.env['carrier.ref.order']
        orders = RefOrder.search(domain)
        carrier_cost = {}
        for order in orders:
            name = order.carrier_id.name
            if name not in carrier_cost:
                carrier_cost[name] = {'carrier': name, 'estimated': 0, 'actual': 0, 'count': 0}
            carrier_cost[name]['estimated'] += order.delivery_charge
            carrier_cost[name]['actual'] += order.real_delivery_charge
            carrier_cost[name]['count'] += 1

        result = list(carrier_cost.values())
        for item in result:
            item['diff'] = item['actual'] - item['estimated']
            item['diff_pct'] = round((item['diff'] / item['estimated']) * 100, 1) if item['estimated'] else 0
        return sorted(result, key=lambda x: x['count'], reverse=True)

    @api.model
    def _get_cod_summary(self, domain):
        """Get COD summary data."""
        RefOrder = self.env['carrier.ref.order']
        cod_domain = domain + [('cash_on_delivery', '=', True)]
        orders = RefOrder.search(cod_domain)
        carrier_cod = {}
        for order in orders:
            name = order.carrier_id.name
            if name not in carrier_cod:
                carrier_cod[name] = {'carrier': name, 'orders': 0, 'amount': 0}
            carrier_cod[name]['orders'] += 1
            carrier_cod[name]['amount'] += order.cash_on_delivery_amount
        return sorted(carrier_cod.values(), key=lambda x: x['amount'], reverse=True)

    @api.model
    def _get_carriers_list(self):
        """Get all active delivery carriers."""
        carriers = self.env['delivery.carrier'].search([
            ('delivery_type', 'not in', ['fixed', 'base_on_rule'])
        ])
        return [{'id': c.id, 'name': c.name, 'delivery_type': c.delivery_type} for c in carriers]

    @api.model
    def _get_standard_status_cards(self, domain):
        """Get order count per standard status for card display."""
        RefOrder = self.env['carrier.ref.order']
        orders = RefOrder.search(domain)
        StandardStatus = self.env['delivery.standard.status']
        statuses = StandardStatus.search([('show_on_dashboard', '=', True)], order='sequence')

        count_map = {}
        for order in orders:
            code = order.mapped_status or '_unmapped'
            count_map[code] = count_map.get(code, 0) + 1

        cards = []
        for status in statuses:
            cards.append({
                'code': status.code,
                'name': status.name,
                'count': count_map.get(status.code, 0),
                'color': status.color or '#6c757d',
            })
        return cards

    @api.model
    def _get_webhook_stats(self, domain, date_from, date_to):
        """Get webhook monitoring statistics."""
        WebhookLog = self.env['delivery.webhook.log']
        logs = WebhookLog.search(domain)

        total = len(logs)
        success_count = len(logs.filtered(lambda l: l.response_status == 'success'))
        error_count = len(logs.filtered(lambda l: l.response_status == 'error'))
        ignored_count = len(logs.filtered(lambda l: l.response_status == 'ignored'))

        # Average processing time
        processing_times = [l.processing_time_ms for l in logs if l.processing_time_ms]
        avg_processing_time = round(sum(processing_times) / len(processing_times)) if processing_times else 0
        max_processing_time = max(processing_times) if processing_times else 0

        # Success rate
        success_rate = round((success_count / total) * 100, 1) if total else 0

        # Per-carrier breakdown
        carrier_stats = defaultdict(lambda: {
            'total': 0, 'success': 0, 'error': 0, 'ignored': 0, 'avg_time': 0, 'times': []
        })
        for log in logs:
            ct = log.carrier_type or 'unknown'
            carrier_stats[ct]['total'] += 1
            if log.response_status == 'success':
                carrier_stats[ct]['success'] += 1
            elif log.response_status == 'error':
                carrier_stats[ct]['error'] += 1
            else:
                carrier_stats[ct]['ignored'] += 1
            if log.processing_time_ms:
                carrier_stats[ct]['times'].append(log.processing_time_ms)

        carrier_breakdown = []
        for carrier_type, data in sorted(carrier_stats.items(), key=lambda x: x[1]['total'], reverse=True):
            avg_time = round(sum(data['times']) / len(data['times'])) if data['times'] else 0
            carrier_breakdown.append({
                'carrier_type': carrier_type,
                'total': data['total'],
                'success': data['success'],
                'error': data['error'],
                'ignored': data['ignored'],
                'avg_time': avg_time,
                'success_rate': round((data['success'] / data['total']) * 100, 1) if data['total'] else 0,
            })

        # Daily webhook volume
        daily_webhooks = {}
        current = date_from
        while current <= date_to:
            daily_webhooks[str(current)] = {'success': 0, 'error': 0, 'ignored': 0}
            current += timedelta(days=1)

        for log in logs:
            day_str = str(log.create_date.date())
            if day_str in daily_webhooks:
                st = log.response_status or 'success'
                if st in daily_webhooks[day_str]:
                    daily_webhooks[day_str][st] += 1

        daily_data = [
            {
                'date': k,
                'success': v['success'],
                'error': v['error'],
                'ignored': v['ignored'],
                'total': v['success'] + v['error'] + v['ignored'],
            }
            for k, v in sorted(daily_webhooks.items())
        ]

        # Recent errors (last 10)
        error_logs = WebhookLog.search(
            domain + [('response_status', '=', 'error')],
            order='create_date desc',
            limit=10,
        )
        recent_errors = [{
            'id': log.id,
            'date': fields.Datetime.to_string(log.create_date),
            'carrier_type': log.carrier_type or '',
            'tracking_ref': log.tracking_ref or '',
            'error_message': log.error_message or '',
            'processing_time_ms': log.processing_time_ms,
        } for log in error_logs]

        return {
            'total': total,
            'success': success_count,
            'error': error_count,
            'ignored': ignored_count,
            'success_rate': success_rate,
            'avg_processing_time': avg_processing_time,
            'max_processing_time': max_processing_time,
            'carrier_breakdown': carrier_breakdown,
            'daily_data': daily_data,
            'recent_errors': recent_errors,
        }

    # ==================== PERFORMANCE ANALYTICS ====================

    @api.model
    def _get_performance_analytics(self, domain, date_from, date_to):
        """Get comprehensive performance analytics for negotiation intelligence."""
        return {
            'cost_efficiency': self._get_cost_efficiency(domain),
            'delivery_speed': self._get_delivery_speed(domain),
            'failure_analysis': self._get_failure_analysis(domain, date_from, date_to),
            'geographic_performance': self._get_geographic_performance(domain),
            'carrier_scorecard': self._get_carrier_scorecard(domain),
        }

    @api.model
    def _get_cost_efficiency(self, domain):
        """Cost efficiency analysis: true cost per successful delivery per carrier.

        True Cost = Total real cost (including failed/returned orders) / Number of successful deliveries.
        This reveals the REAL cost of using a carrier, not just the per-shipment cost.
        """
        RefOrder = self.env['carrier.ref.order']
        orders = RefOrder.search(domain)
        carrier_data = {}

        for order in orders:
            cid = order.carrier_id.id
            if cid not in carrier_data:
                carrier_data[cid] = {
                    'carrier_id': cid,
                    'carrier_name': order.carrier_id.name,
                    'delivery_type': order.delivery_type,
                    'total_orders': 0,
                    'delivered_count': 0,
                    'failed_count': 0,
                    'total_est_cost': 0,
                    'total_real_cost': 0,
                    'cost_overrun_count': 0,
                    'cost_overrun_total': 0,
                }
            d = carrier_data[cid]
            d['total_orders'] += 1
            d['total_est_cost'] += order.delivery_charge or 0
            d['total_real_cost'] += order.real_delivery_charge or 0

            # Cost overrun
            if order.real_delivery_charge and order.delivery_charge:
                diff = order.real_delivery_charge - order.delivery_charge
                if diff > 0:
                    d['cost_overrun_count'] += 1
                    d['cost_overrun_total'] += diff

            # Status classification
            if order.mapped_status_id:
                if order.mapped_status_id.code == 'delivered':
                    d['delivered_count'] += 1
                elif order.mapped_status_id.code in ('failed', 'cancelled', 'returned'):
                    d['failed_count'] += 1
            else:
                completed_codes = ['501', 'COMPLETED', '6']
                failed_codes = ['503', 'CANCELED', 'REJECTED', 'EXPIRED', '-1', 'CANCELLED']
                code = order.delivery_status_id.code or ''
                if code in completed_codes:
                    d['delivered_count'] += 1
                elif code in failed_codes:
                    d['failed_count'] += 1

        result = []
        for d in sorted(carrier_data.values(), key=lambda x: x['total_orders'], reverse=True):
            delivered = d['delivered_count']
            avg_cost = round(d['total_real_cost'] / d['total_orders'], 0) if d['total_orders'] else 0
            true_cost = round(d['total_real_cost'] / delivered, 0) if delivered else 0
            overrun_pct = round((d['cost_overrun_total'] / d['total_est_cost']) * 100, 1) if d['total_est_cost'] else 0
            success_rate = round((delivered / d['total_orders']) * 100, 1) if d['total_orders'] else 0

            result.append({
                'carrier_id': d['carrier_id'],
                'carrier_name': d['carrier_name'],
                'delivery_type': d['delivery_type'],
                'total_orders': d['total_orders'],
                'delivered': delivered,
                'failed': d['failed_count'],
                'success_rate': success_rate,
                'avg_cost_per_shipment': avg_cost,
                'true_cost_per_delivery': true_cost,
                'total_est_cost': d['total_est_cost'],
                'total_real_cost': d['total_real_cost'],
                'cost_overrun_count': d['cost_overrun_count'],
                'cost_overrun_pct': overrun_pct,
                'waste_cost': d['total_real_cost'] - (avg_cost * delivered) if delivered else 0,
            })
        return result

    @api.model
    def _get_delivery_speed(self, domain):
        """Delivery speed analysis: average time from order creation to delivered status.

        Uses write_date of the carrier.ref.order when it reaches 'delivered' mapped_status.
        """
        RefOrder = self.env['carrier.ref.order']
        # Only delivered orders
        delivered_domain = domain + [('mapped_status', '=', 'delivered')]
        orders = RefOrder.search(delivered_domain)
        carrier_data = {}

        for order in orders:
            cid = order.carrier_id.id
            if cid not in carrier_data:
                carrier_data[cid] = {
                    'carrier_name': order.carrier_id.name,
                    'delivery_type': order.delivery_type,
                    'durations': [],
                }
            if order.create_date and order.write_date:
                duration_hours = (order.write_date - order.create_date).total_seconds() / 3600
                if duration_hours > 0:
                    carrier_data[cid]['durations'].append(duration_hours)

        result = []
        for cid, d in carrier_data.items():
            durations = d['durations']
            if not durations:
                continue
            avg_hours = round(sum(durations) / len(durations), 1)
            min_hours = round(min(durations), 1)
            max_hours = round(max(durations), 1)
            # Median
            sorted_d = sorted(durations)
            mid = len(sorted_d) // 2
            median_hours = round(
                (sorted_d[mid] + sorted_d[mid - 1]) / 2 if len(sorted_d) % 2 == 0 else sorted_d[mid],
                1
            )
            # SLA: percentage delivered within 48 hours
            within_48h = len([x for x in durations if x <= 48])
            sla_48h_pct = round((within_48h / len(durations)) * 100, 1)

            result.append({
                'carrier_name': d['carrier_name'],
                'delivery_type': d['delivery_type'],
                'total_delivered': len(durations),
                'avg_hours': avg_hours,
                'median_hours': median_hours,
                'min_hours': min_hours,
                'max_hours': max_hours,
                'sla_48h_pct': sla_48h_pct,
            })
        return sorted(result, key=lambda x: x['avg_hours'])

    @api.model
    def _get_failure_analysis(self, domain, date_from, date_to):
        """Failure pattern analysis: failure trends over time per carrier."""
        RefOrder = self.env['carrier.ref.order']
        failed_domain = domain + [('mapped_status', 'in', ['failed', 'cancelled', 'returned'])]
        orders = RefOrder.search(failed_domain)

        # Weekly failure trend
        weekly = defaultdict(lambda: defaultdict(int))
        failure_reasons = defaultdict(lambda: defaultdict(int))

        for order in orders:
            week = order.create_date.strftime('%Y-W%W')
            carrier_name = order.carrier_id.name
            weekly[week][carrier_name] += 1

            # Classify failure type by mapped_status
            status_name = order.mapped_status_id.name if order.mapped_status_id else 'Unknown'
            failure_reasons[carrier_name][status_name] += 1

        # Build weekly trend
        all_weeks = sorted(weekly.keys())
        all_carriers = set()
        for w in weekly.values():
            all_carriers.update(w.keys())
        all_carriers = sorted(all_carriers)

        weekly_data = []
        for week in all_weeks:
            entry = {'week': week}
            for carrier in all_carriers:
                entry[carrier] = weekly[week].get(carrier, 0)
            weekly_data.append(entry)

        # Build failure reasons
        reasons_data = []
        for carrier, reasons in sorted(failure_reasons.items()):
            total = sum(reasons.values())
            reasons_list = []
            for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
                reasons_list.append({
                    'reason': reason,
                    'count': count,
                    'pct': round((count / total) * 100, 1) if total else 0,
                })
            reasons_data.append({
                'carrier': carrier,
                'total_failures': total,
                'reasons': reasons_list,
            })

        return {
            'weekly_trend': weekly_data,
            'carriers': all_carriers,
            'failure_reasons': sorted(reasons_data, key=lambda x: x['total_failures'], reverse=True),
            'total_failures': len(orders),
        }

    @api.model
    def _get_geographic_performance(self, domain):
        """Geographic performance: success rate and speed by destination province."""
        RefOrder = self.env['carrier.ref.order']
        orders = RefOrder.search(domain)
        geo_data = {}

        for order in orders:
            partner = order.picking_id.partner_id if order.picking_id else None
            if not partner:
                continue
            province = partner.state_id.name if partner.state_id else 'Unknown'
            carrier_name = order.carrier_id.name
            key = (province, carrier_name)

            if key not in geo_data:
                geo_data[key] = {
                    'province': province,
                    'carrier': carrier_name,
                    'total': 0,
                    'delivered': 0,
                    'failed': 0,
                    'total_cost': 0,
                }
            g = geo_data[key]
            g['total'] += 1
            g['total_cost'] += order.real_delivery_charge or order.delivery_charge or 0

            if order.mapped_status_id:
                if order.mapped_status_id.code == 'delivered':
                    g['delivered'] += 1
                elif order.mapped_status_id.code in ('failed', 'cancelled', 'returned'):
                    g['failed'] += 1

        result = []
        for g in geo_data.values():
            g['success_rate'] = round((g['delivered'] / g['total']) * 100, 1) if g['total'] else 0
            g['avg_cost'] = round(g['total_cost'] / g['total'], 0) if g['total'] else 0
            result.append(g)

        return sorted(result, key=lambda x: (-x['total'], x['province']))

    @api.model
    def _get_carrier_scorecard(self, domain):
        """Carrier Scorecard: weighted scoring across all metrics.

        Score = w1×Success + w2×Speed + w3×CostEfficiency + w4×Reliability
        This is the core "negotiation intelligence" — a single number to compare carriers.
        """
        cost_data = self._get_cost_efficiency(domain)
        speed_data = self._get_delivery_speed(domain)

        # Build speed lookup
        speed_lookup = {d['carrier_name']: d for d in speed_data}

        scorecards = []
        for carrier in cost_data:
            name = carrier['carrier_name']
            speed = speed_lookup.get(name, {})

            # Normalize scores to 0-100
            success_score = min(carrier['success_rate'], 100)

            # Speed score: lower is better. 24h=100, 72h=50, 168h(7days)=0
            avg_h = speed.get('avg_hours', 168)
            speed_score = max(0, min(100, 100 - ((avg_h - 24) / (168 - 24)) * 100))

            # Cost efficiency: lower overrun = better. 0% overrun=100, 20%+=0
            overrun = carrier['cost_overrun_pct']
            cost_score = max(0, min(100, 100 - (overrun / 20) * 100))

            # Reliability: percentage of orders that don't have cost overrun
            reliability_score = 0
            if carrier['total_orders']:
                reliability_score = round(
                    ((carrier['total_orders'] - carrier['cost_overrun_count']) / carrier['total_orders']) * 100,
                    1
                )

            # Weighted final score
            final_score = round(
                0.35 * success_score
                + 0.25 * speed_score
                + 0.25 * cost_score
                + 0.15 * reliability_score,
                1
            )

            scorecards.append({
                'carrier_name': name,
                'delivery_type': carrier['delivery_type'],
                'total_orders': carrier['total_orders'],
                'success_score': round(success_score, 1),
                'speed_score': round(speed_score, 1),
                'cost_score': round(cost_score, 1),
                'reliability_score': round(reliability_score, 1),
                'final_score': final_score,
                # Raw data for tooltips
                'success_rate': carrier['success_rate'],
                'avg_hours': speed.get('avg_hours', 0),
                'true_cost': carrier['true_cost_per_delivery'],
                'overrun_pct': carrier['cost_overrun_pct'],
            })

        return sorted(scorecards, key=lambda x: x['final_score'], reverse=True)

    def init(self):
        """No table needed — this is a virtual model."""
        pass

