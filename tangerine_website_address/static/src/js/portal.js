/** @odoo-module */
import portalDetails from "@portal/js/portal";

portalDetails.include({
    events: Object.assign({}, portalDetails.prototype.events, {
        'change select[name="state_id"]': '_onStateChange',
        'change select[name="district_id"]': '_onDistrictChange',
        'change select[name="country_id"]': '_onCountryChange',
    }),

    /**
     * @override
     */
    start: function () {
        var def = this._super.apply(this, arguments);
        this.$district = this.$('select[name="district_id"]');
        this.$districtOptions = this.$district.filter(':enabled').find('option:not(:first)');

        this.$ward = this.$('select[name="ward_id"]');
        this.$wardOptions = this.$ward.filter(':enabled').find('option:not(:first)');
        this._adaptDistrictForm();
        this._adaptWardForm();
        return def;
    },

    _adaptAddressForm: function () {
        this._super.apply(this, arguments);
        this._resetDistrictWard();
    },

    _onCountryChange: function () {
        this._adaptAddressForm();
    },

    _adaptDistrictForm: function () {
        var stateID = this.$state.val() || 0;

        this.$districtOptions.detach();
        var $displayedDistrict = this.$districtOptions.filter('[data-state_id=' + stateID + ']');
        var nbDistrict = $displayedDistrict.appendTo(this.$district).show().length;
        this.$district.parent().toggle(nbDistrict >= 1);

        // this._resetWard();
    },

    _adaptWardForm: function () {
        var districtID = this.$district.val() || 0;

        this.$wardOptions.detach();
        var $displayedWard = this.$wardOptions.filter('[data-district_id=' + districtID + ']');
        var nbWard = $displayedWard.appendTo(this.$ward).show().length;
        this.$ward.parent().toggle(nbWard >= 1);
    },

    _resetDistrictWard: function () {
        if (this.$district && this.$district.length) {
            this.$district.val('').parent().hide();
        }
        if (this.$ward && this.$ward.length) {
            this.$ward.val('').parent().hide();
        }
    },

    _resetWard: function () {
        if (this.$ward && this.$ward.length) {
            this.$ward.val('').parent().hide();
        }
    },

    _onStateChange: function () {
        this._adaptDistrictForm();
    },

    _onDistrictChange: function () {
        this._adaptWardForm();
    },
});
