import { Component, useState, onWillStart, useRef, useEffect, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { loadBundle } from "@web/core/assets";
import { getColor } from "@web/core/colors/colors";
import { cookie } from "@web/core/browser/cookie";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { DateTimeInput } from "@web/core/datetime/datetime_input";

const { DateTime } = luxon;

/**
 * Date period options — same structure as spreadsheet.DateFilterDropdown
 */
const DATE_OPTIONS = [
    { id: "today", label: _t("Today"), separator: false },
    { id: "yesterday", label: _t("Yesterday"), separator: true },
    { id: "last_7_days", label: _t("Last 7 Days") },
    { id: "last_30_days", label: _t("Last 30 Days") },
    { id: "last_90_days", label: _t("Last 90 Days"), separator: true },
    { id: "month_to_date", label: _t("Month to Date") },
    { id: "last_month", label: _t("Last Month"), separator: true },
    { id: "year_to_date", label: _t("Year to Date") },
    { id: "last_12_months", label: _t("Last 12 Months"), separator: true },
    { id: "all_time", label: _t("All time") },
    { id: "custom_range", label: _t("Custom Range") },
];

/**
 * Compute from/to dates from a period ID.
 */
function getDateRange(periodId, customFrom, customTo) {
    const now = DateTime.local();
    const startOfNextDay = now.plus({ days: 1 }).startOf("day");
    switch (periodId) {
        case "today":
            return { from: now.startOf("day"), to: now.endOf("day") };
        case "yesterday":
            return {
                from: now.minus({ days: 1 }).startOf("day"),
                to: now.minus({ days: 1 }).endOf("day"),
            };
        case "last_7_days":
            return { from: startOfNextDay.minus({ days: 7 }), to: now.endOf("day") };
        case "last_30_days":
            return { from: startOfNextDay.minus({ days: 30 }), to: now.endOf("day") };
        case "last_90_days":
            return { from: startOfNextDay.minus({ days: 90 }), to: now.endOf("day") };
        case "month_to_date":
            return { from: now.startOf("month"), to: now.endOf("day") };
        case "last_month":
            return {
                from: now.minus({ months: 1 }).startOf("month"),
                to: now.minus({ months: 1 }).endOf("month"),
            };
        case "year_to_date":
            return { from: now.startOf("year"), to: now.endOf("day") };
        case "last_12_months":
            return {
                from: startOfNextDay.minus({ months: 12 }).startOf("month"),
                to: startOfNextDay.minus({ months: 1 }).endOf("month"),
            };
        case "custom_range":
            return {
                from: customFrom ? DateTime.fromISO(customFrom) : now.startOf("month"),
                to: customTo ? DateTime.fromISO(customTo) : now.endOf("day"),
            };
        case "all_time":
        default:
            return { from: null, to: null };
    }
}

/**
 * Get a display label for a period + optional navigate prev/next for relative periods.
 */
function getPeriodLabel(periodId) {
    const opt = DATE_OPTIONS.find((o) => o.id === periodId);
    return opt ? opt.label : _t("All time");
}

/**
 * Navigate a period forward/backward in time (returns ISO strings for custom_range).
 */
function navigatePeriod(periodId, direction, currentFrom, currentTo) {
    const now = DateTime.local();
    if (periodId === "custom_range" && currentFrom && currentTo) {
        const from = DateTime.fromISO(currentFrom);
        const to = DateTime.fromISO(currentTo);
        const days = Math.round(to.diff(from, "days").days) + 1;
        const offset = direction * days;
        return {
            from: from.plus({ days: offset }).toISODate(),
            to: to.plus({ days: offset }).toISODate(),
        };
    }
    // For relative periods, shift into a custom_range
    const range = getDateRange(periodId);
    if (!range.from || !range.to) return null;

    const days = Math.round(range.to.diff(range.from, "days").days) + 1;
    const offset = direction * days;
    return {
        from: range.from.plus({ days: offset }).toISODate(),
        to: range.to.plus({ days: offset }).toISODate(),
    };
}

class DeliveryDashboard extends Component {
    static template = "tangerine_delivery_base.DeliveryDashboard";
    static components = { Dropdown, DropdownItem, DateTimeInput };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            data: null,
            loading: true,
            period: "last_7_days",
            customFrom: "",
            customTo: "",
            carrierId: null,
            mode: "delivery", // 'delivery' or 'webhook'
        });

        // Canvas refs for Chart.js
        this.trendChartRef = useRef("trendChart");
        this.statusChartRef = useRef("statusChart");
        this.costChartRef = useRef("costChart");
        this.webhookChartRef = useRef("webhookChart");
        this.webhookStatusChartRef = useRef("webhookStatusChart");
        this.webhookResponseChartRef = useRef("webhookResponseChart");
        this.scorecardChartRef = useRef("scorecardChart");
        this.failureTrendChartRef = useRef("failureTrendChart");

        // Chart instances
        this.trendChart = null;
        this.statusChart = null;
        this.costChart = null;
        this.webhookChart = null;
        this.webhookStatusChart = null;
        this.webhookResponseChart = null;
        this.scorecardChart = null;
        this.failureTrendChart = null;

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await this.loadDashboard();
        });

        useEffect(
            () => {
                if (this.state.data && !this.state.loading) {
                    if (this.state.mode === "delivery") {
                        this._renderTrendChart();
                        this._renderStatusChart();
                        this._renderCostChart();
                    } else if (this.state.mode === "webhook") {
                        this._renderWebhookChart();
                        this._renderWebhookStatusChart();
                        this._renderWebhookResponseChart();
                    } else if (this.state.mode === "performance") {
                        this._renderScorecardChart();
                        this._renderFailureTrendChart();
                    }
                }
            },
            () => [this.state.data, this.state.loading, this.state.mode]
        );

        onWillUnmount(() => {
            this._destroyCharts();
        });
    }

    _destroyCharts() {
        if (this.trendChart) { this.trendChart.destroy(); this.trendChart = null; }
        if (this.statusChart) { this.statusChart.destroy(); this.statusChart = null; }
        if (this.costChart) { this.costChart.destroy(); this.costChart = null; }
        if (this.webhookChart) { this.webhookChart.destroy(); this.webhookChart = null; }
        if (this.webhookStatusChart) { this.webhookStatusChart.destroy(); this.webhookStatusChart = null; }
        if (this.webhookResponseChart) { this.webhookResponseChart.destroy(); this.webhookResponseChart = null; }
        if (this.scorecardChart) { this.scorecardChart.destroy(); this.scorecardChart = null; }
        if (this.failureTrendChart) { this.failureTrendChart.destroy(); this.failureTrendChart = null; }
    }

    _renderTrendChart() {
        if (!this.trendChartRef.el || !this.state.data?.daily_orders?.length) return;
        if (this.trendChart) this.trendChart.destroy();

        const colorScheme = cookie.get("color_scheme");
        const data = this.state.data.daily_orders;
        const labels = data.map((d) => this.formatShortDate(d.date));
        const values = data.map((d) => d.count);
        const lineColor = getColor(0, colorScheme);

        this.trendChart = new Chart(this.trendChartRef.el, {
            type: "line",
            data: {
                labels,
                datasets: [{
                    label: _t("Orders"),
                    data: values,
                    borderColor: lineColor,
                    backgroundColor: lineColor + "30",
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2.5,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    pointBackgroundColor: lineColor,
                    pointBorderColor: "#fff",
                    pointBorderWidth: 1.5,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: "index", intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: (items) => data[items[0].dataIndex]?.date || "",
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { maxRotation: 0, autoSkipPadding: 8 },
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: "rgba(0,0,0,.06)" },
                    },
                },
                animation: { duration: 600 },
            },
        });
    }

    _renderStatusChart() {
        if (!this.statusChartRef.el || !this.state.data?.status_distribution?.length) return;
        if (this.statusChart) this.statusChart.destroy();

        const colorScheme = cookie.get("color_scheme");
        const data = this.state.data.status_distribution;
        const labels = data.map((d) => d.status);
        const values = data.map((d) => d.count);
        const colors = data.map((_, i) => getColor(i, colorScheme, data.length));

        this.statusChart = new Chart(this.statusChartRef.el, {
            type: "doughnut",
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 2,
                    hoverOffset: 8,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "right",
                        labels: { padding: 12, usePointStyle: true, pointStyle: 'circle' },
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const total = values.reduce((a, b) => a + b, 0);
                                const pct = total ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                                return ` ${ctx.label}: ${ctx.raw} (${pct}%)`;
                            },
                        },
                    },
                },
                animation: { duration: 600 },
            },
        });
    }

    _renderCostChart() {
        if (!this.costChartRef.el || !this.state.data?.cost_comparison?.length) return;
        if (this.costChart) this.costChart.destroy();

        const data = this.state.data.cost_comparison;
        const labels = data.map((d) => d.carrier);

        // Complementary pair: blue (estimated) vs amber (actual)
        const estColor = "#4078c0";
        const actColor = "#e6994a";

        this.costChart = new Chart(this.costChartRef.el, {
            type: "bar",
            data: {
                labels,
                datasets: [
                    {
                        label: _t("Estimated"),
                        data: data.map((d) => d.estimated),
                        backgroundColor: estColor + "cc",
                        borderColor: estColor,
                        borderWidth: 1,
                        borderRadius: 3,
                        borderSkipped: false,
                    },
                    {
                        label: _t("Actual"),
                        data: data.map((d) => d.actual),
                        backgroundColor: actColor + "cc",
                        borderColor: actColor,
                        borderWidth: 1,
                        borderRadius: 3,
                        borderSkipped: false,
                    },
                ],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "top",
                        align: "end",
                        labels: { usePointStyle: true, pointStyle: 'circle', padding: 16 },
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.dataset.label}: ${this.formatCurrency(ctx.raw)}`,
                        },
                    },
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: "rgba(0,0,0,.06)" },
                        ticks: {
                            callback: (v) => this.formatCurrency(v),
                        },
                    },
                    y: {
                        grid: { display: false },
                    },
                },
                animation: { duration: 600 },
            },
        });
    }

    get dateOptions() {
        return DATE_OPTIONS;
    }

    get modeLabel() {
        if (this.state.mode === "delivery") return _t("Delivery Analytics");
        if (this.state.mode === "webhook") return _t("Webhook Monitoring");
        return _t("Performance Analytics");
    }

    get modeIcon() {
        if (this.state.mode === "delivery") return "fa-truck";
        if (this.state.mode === "webhook") return "fa-rss";
        return "fa-trophy";
    }

    selectMode(mode) {
        this.state.mode = mode;
    }

    get periodLabel() {
        if (this.state.period === "custom_range" && this.state.customFrom && this.state.customTo) {
            const from = DateTime.fromISO(this.state.customFrom);
            const to = DateTime.fromISO(this.state.customTo);
            return `${from.toLocaleString(DateTime.DATE_SHORT)} – ${to.toLocaleString(DateTime.DATE_SHORT)}`;
        }
        return getPeriodLabel(this.state.period);
    }

    isSelected(option) {
        return this.state.period === option.id;
    }

    async selectPeriod(option) {
        this.state.period = option.id;
        if (option.id !== "custom_range") {
            this.state.customFrom = "";
            this.state.customTo = "";
        }
        await this.loadDashboard();
    }

    get customDateFrom() {
        return this.state.customFrom ? DateTime.fromISO(this.state.customFrom) : undefined;
    }

    get customDateTo() {
        return this.state.customTo ? DateTime.fromISO(this.state.customTo) : undefined;
    }

    async setCustomFrom(date) {
        this.state.customFrom = date ? date.toISODate() : "";
        this.state.period = "custom_range";
        if (this.state.customFrom && this.state.customTo) {
            await this.loadDashboard();
        }
    }

    async setCustomTo(date) {
        this.state.customTo = date ? date.toISODate() : "";
        this.state.period = "custom_range";
        if (this.state.customFrom && this.state.customTo) {
            await this.loadDashboard();
        }
    }

    async onNavigatePrevious() {
        this._navigate(-1);
    }

    async onNavigateNext() {
        this._navigate(1);
    }

    async _navigate(direction) {
        const result = navigatePeriod(
            this.state.period,
            direction,
            this.state.customFrom,
            this.state.customTo
        );
        if (result) {
            this.state.period = "custom_range";
            this.state.customFrom = result.from;
            this.state.customTo = result.to;
            await this.loadDashboard();
        }
    }

    _getDateParams() {
        const range = getDateRange(this.state.period, this.state.customFrom, this.state.customTo);
        return {
            date_from: range.from ? range.from.toISODate() : null,
            date_to: range.to ? range.to.toISODate() : null,
            carrier_id: this.state.carrierId,
        };
    }

    async loadDashboard() {
        this.state.loading = true;
        try {
            const data = await this.orm.call(
                "delivery.dashboard",
                "get_dashboard_data",
                [],
                this._getDateParams()
            );
            this.state.data = data;
        } catch (e) {
            console.error("Dashboard load error:", e);
        }
        this.state.loading = false;
    }

    get carrierLabel() {
        if (!this.state.carrierId || !this.state.data?.carriers) {
            return _t("All Carriers");
        }
        const carrier = this.state.data.carriers.find((c) => c.id === this.state.carrierId);
        return carrier ? carrier.name : _t("All Carriers");
    }

    async selectCarrier(carrierId) {
        this.state.carrierId = carrierId;
        await this.loadDashboard();
    }

    formatCurrency(value) {
        const code = this.state.data?.currency_code || "VND";
        const symbol = this.state.data?.currency_symbol || "";
        const position = this.state.data?.currency_position || "after";
        const formatted = new Intl.NumberFormat("vi-VN", {
            maximumFractionDigits: 0,
        }).format(value || 0);
        if (symbol) {
            return position === "before" ? `${symbol}${formatted}` : `${formatted} ${symbol}`;
        }
        return new Intl.NumberFormat("vi-VN", {
            style: "currency",
            currency: code,
            maximumFractionDigits: 0,
        }).format(value || 0);
    }

    formatNumber(value) {
        return new Intl.NumberFormat("vi-VN").format(value || 0);
    }

    getBarWidth(value, max) {
        return max > 0 ? Math.round((value / max) * 100) : 0;
    }

    getContrastColor(hex) {
        if (!hex) return "#212529";
        hex = hex.replace("#", "");
        const r = parseInt(hex.substring(0, 2), 16);
        const g = parseInt(hex.substring(2, 4), 16);
        const b = parseInt(hex.substring(4, 6), 16);
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        return luminance > 0.55 ? "#212529" : "#ffffff";
    }

    getMaxDaily() {
        if (!this.state.data || !this.state.data.daily_orders) return 1;
        return Math.max(...this.state.data.daily_orders.map((d) => d.count), 1);
    }

    formatShortDate(dateStr) {
        const d = new Date(dateStr);
        return `${d.getDate()}/${d.getMonth() + 1}`;
    }

    async openCarrierOrders(carrierId) {
        const params = this._getDateParams();
        const domain = [["carrier_id", "=", carrierId]];
        if (params.date_from) domain.push(["create_date", ">=", params.date_from]);
        if (params.date_to) domain.push(["create_date", "<=", params.date_to]);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Carrier Orders"),
            res_model: "carrier.ref.order",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain,
        });
    }

    async openAllOrders() {
        const params = this._getDateParams();
        const domain = [];
        if (params.date_from) domain.push(["create_date", ">=", params.date_from]);
        if (params.date_to) domain.push(["create_date", "<=", params.date_to]);
        if (params.carrier_id) domain.push(["carrier_id", "=", params.carrier_id]);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("All Delivery Orders"),
            res_model: "carrier.ref.order",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain,
        });
    }

    async openCodOrders() {
        const params = this._getDateParams();
        const domain = [["cash_on_delivery", "=", true]];
        if (params.date_from) domain.push(["create_date", ">=", params.date_from]);
        if (params.date_to) domain.push(["create_date", "<=", params.date_to]);
        if (params.carrier_id) domain.push(["carrier_id", "=", params.carrier_id]);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("COD Orders"),
            res_model: "carrier.ref.order",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain,
        });
    }

    async openStatusOrders(statusCode) {
        const params = this._getDateParams();
        const domain = [["mapped_status", "=", statusCode]];
        if (params.date_from) domain.push(["create_date", ">=", params.date_from]);
        if (params.date_to) domain.push(["create_date", "<=", params.date_to]);
        if (params.carrier_id) domain.push(["carrier_id", "=", params.carrier_id]);

        const card = this.state.data?.standard_status_cards?.find((c) => c.code === statusCode);
        const name = card ? card.name : statusCode;

        this.action.doAction({
            type: "ir.actions.act_window",
            name: name,
            res_model: "carrier.ref.order",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain,
        });
    }

    // ========== WEBHOOK MONITORING ==========

    _renderWebhookChart() {
        if (!this.webhookChartRef.el || !this.state.data?.webhook_stats?.daily_data?.length) return;
        if (this.webhookChart) this.webhookChart.destroy();

        const data = this.state.data.webhook_stats.daily_data;
        const labels = data.map((d) => this.formatShortDate(d.date));

        this.webhookChart = new Chart(this.webhookChartRef.el, {
            type: "line",
            data: {
                labels,
                datasets: [
                    {
                        label: _t("Success"),
                        data: data.map((d) => d.success),
                        borderColor: "#28a745",
                        backgroundColor: "#28a74520",
                        fill: true,
                        tension: 0.35,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        borderWidth: 2,
                    },
                    {
                        label: _t("Error"),
                        data: data.map((d) => d.error),
                        borderColor: "#dc3545",
                        backgroundColor: "#dc354520",
                        fill: true,
                        tension: 0.35,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        borderWidth: 2,
                    },
                    {
                        label: _t("Ignored"),
                        data: data.map((d) => d.ignored),
                        borderColor: "#ffc107",
                        backgroundColor: "#ffc10720",
                        fill: true,
                        tension: 0.35,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        borderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "top",
                        align: "end",
                        labels: { usePointStyle: true, pointStyle: "circle", padding: 14 },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { maxRotation: 0, autoSkipPadding: 8 },
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: "rgba(0,0,0,.06)" },
                    },
                },
                animation: { duration: 600 },
            },
        });
    }

    _renderWebhookStatusChart() {
        if (!this.webhookStatusChartRef.el || !this.state.data?.webhook_stats?.total) return;
        if (this.webhookStatusChart) this.webhookStatusChart.destroy();

        const stats = this.state.data.webhook_stats;
        this.webhookStatusChart = new Chart(this.webhookStatusChartRef.el, {
            type: "doughnut",
            data: {
                labels: [_t("Success"), _t("Error"), _t("Ignored")],
                datasets: [{
                    data: [stats.success, stats.error, stats.ignored],
                    backgroundColor: ["#28a745", "#dc3545", "#ffc107"],
                    borderWidth: 2,
                    borderColor: "#fff",
                    hoverOffset: 6,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "60%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { usePointStyle: true, pointStyle: "circle", padding: 14 },
                    },
                },
                animation: { duration: 600 },
            },
        });
    }

    _renderWebhookResponseChart() {
        if (!this.webhookResponseChartRef.el || !this.state.data?.webhook_stats?.carrier_breakdown?.length) return;
        if (this.webhookResponseChart) this.webhookResponseChart.destroy();

        const breakdown = this.state.data.webhook_stats.carrier_breakdown;
        const labels = breakdown.map((c) => c.carrier_type);
        const avgTimes = breakdown.map((c) => c.avg_time);

        this.webhookResponseChart = new Chart(this.webhookResponseChartRef.el, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: _t("Avg Response (ms)"),
                    data: avgTimes,
                    backgroundColor: avgTimes.map((t) =>
                        t <= 200 ? "#28a74599" : t <= 500 ? "#ffc10799" : "#dc354599"
                    ),
                    borderColor: avgTimes.map((t) =>
                        t <= 200 ? "#28a745" : t <= 500 ? "#ffc107" : "#dc3545"
                    ),
                    borderWidth: 1,
                    borderRadius: 4,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: "y",
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.raw}ms`,
                        },
                    },
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: "rgba(0,0,0,.06)" },
                        ticks: { callback: (v) => `${v}ms` },
                    },
                    y: {
                        grid: { display: false },
                    },
                },
                animation: { duration: 600 },
            },
        });
    }

    async openWebhookLogs() {
        const params = this._getDateParams();
        const domain = [];
        if (params.date_from) domain.push(["create_date", ">=", params.date_from]);
        if (params.date_to) domain.push(["create_date", "<=", params.date_to]);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Webhook Logs"),
            res_model: "delivery.webhook.log",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain,
        });
    }

    async openWebhookErrors() {
        const params = this._getDateParams();
        const domain = [["response_status", "=", "error"]];
        if (params.date_from) domain.push(["create_date", ">=", params.date_from]);
        if (params.date_to) domain.push(["create_date", "<=", params.date_to]);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Webhook Errors"),
            res_model: "delivery.webhook.log",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain,
        });
    }

    async openWebhookLogDetail(logId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Webhook Log"),
            res_model: "delivery.webhook.log",
            res_id: logId,
            view_mode: "form",
            views: [[false, "form"]],
        });
    }

    // ========== PERFORMANCE ANALYTICS ==========

    _renderScorecardChart() {
        if (!this.scorecardChartRef.el || !this.state.data?.performance?.carrier_scorecard?.length) return;
        if (this.scorecardChart) this.scorecardChart.destroy();

        const colorScheme = cookie.get("color_scheme");
        const data = this.state.data.performance.carrier_scorecard;
        const labels = [_t("Success"), _t("Speed"), _t("Cost"), _t("Reliability")];
        const datasets = data.map((carrier, idx) => ({
            label: carrier.carrier_name,
            data: [carrier.success_score, carrier.speed_score, carrier.cost_score, carrier.reliability_score],
            borderColor: getColor(idx, colorScheme, data.length),
            backgroundColor: getColor(idx, colorScheme, data.length) + "30",
            borderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            fill: true,
        }));

        this.scorecardChart = new Chart(this.scorecardChartRef.el, {
            type: "radar",
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { usePointStyle: true, pointStyle: "circle", padding: 14 },
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.dataset.label}: ${ctx.raw}/100`,
                        },
                    },
                },
                scales: {
                    r: {
                        min: 0,
                        max: 100,
                        ticks: { stepSize: 20, display: true, backdropColor: "transparent" },
                        pointLabels: { font: { size: 12, weight: "bold" } },
                        grid: { color: "rgba(0,0,0,.08)" },
                        angleLines: { color: "rgba(0,0,0,.08)" },
                    },
                },
                animation: { duration: 600 },
            },
        });
    }

    _renderFailureTrendChart() {
        if (!this.failureTrendChartRef.el) return;
        const analysis = this.state.data?.performance?.failure_analysis;
        if (!analysis?.weekly_trend?.length) return;
        if (this.failureTrendChart) this.failureTrendChart.destroy();

        const colorScheme = cookie.get("color_scheme");
        const weeklyData = analysis.weekly_trend;
        const carriers = analysis.carriers || [];
        const labels = weeklyData.map((d) => d.week);

        const datasets = carriers.map((carrier, idx) => ({
            label: carrier,
            data: weeklyData.map((d) => d[carrier] || 0),
            borderColor: getColor(idx, colorScheme, carriers.length),
            backgroundColor: getColor(idx, colorScheme, carriers.length) + "30",
            fill: false,
            tension: 0.35,
            borderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 5,
        }));

        this.failureTrendChart = new Chart(this.failureTrendChartRef.el, {
            type: "line",
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: "index", intersect: false },
                plugins: {
                    legend: {
                        position: "top",
                        align: "end",
                        labels: { usePointStyle: true, pointStyle: "circle", padding: 14 },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { maxRotation: 45, autoSkipPadding: 8 },
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: "rgba(0,0,0,.06)" },
                        title: { display: true, text: _t("Failures") },
                    },
                },
                animation: { duration: 600 },
            },
        });
    }

    getScoreColor(score) {
        if (score >= 80) return "text-success";
        if (score >= 60) return "text-warning";
        return "text-danger";
    }

    getScoreBadgeClass(score) {
        if (score >= 80) return "text-bg-success";
        if (score >= 60) return "text-bg-warning";
        return "text-bg-danger";
    }

    getScoreBarWidth(score) {
        return Math.min(Math.round(score), 100);
    }

    getScoreBarColor(score) {
        if (score >= 80) return "#198754";
        if (score >= 60) return "#ffc107";
        return "#dc3545";
    }

    formatHours(hours) {
        if (!hours) return "-";
        if (hours < 1) return `${Math.round(hours * 60)}m`;
        if (hours < 24) return `${Math.round(hours)}h`;
        const days = Math.floor(hours / 24);
        const remainHours = Math.round(hours % 24);
        return remainHours > 0 ? `${days}d ${remainHours}h` : `${days}d`;
    }
}

registry.category("actions").add("delivery_dashboard", DeliveryDashboard);
