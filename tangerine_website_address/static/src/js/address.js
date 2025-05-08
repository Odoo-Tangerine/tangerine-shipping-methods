/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";
import websiteSaleAddress from '@website_sale/js/address';

websiteSaleAddress.include({
    events: Object.assign({}, websiteSaleAddress.prototype.events, {
        'change select[name="district_id"]': '_onChangeDistrict',
    }),

    // start() {
    //     const def = this._super(...arguments);
    //     this._changeState(true);
    //     this._changeDistrict(true);
    //     return def;
    // },

    _onChangeState: function (ev) {
        let def = this._super.apply(this, arguments);
        if (this.countryCode !== 'VN') {
            return def;
        }
        this._changeStateVN()
    },

    _changeStateVN: function (init = false) {
        const stateId = parseInt(this.addressForm.state_id.value);
        if (!stateId) { return; }
        return rpc(`/shop/district_info/${stateId}`).then((data) => {
            let selectDistricts = this.addressForm.district_id;
            if (!init || selectDistricts.options.length === 1) {
                if (data.districts.length) {
                    selectDistricts.options.length = 1;
                    data.districts.forEach((district) => {
                        let option = new Option(district[1], district[0]);
                        option.setAttribute('data-code', district[2]);
                        selectDistricts.appendChild(option);
                    });
                    this._showInput('district_id');
                } else {
                    this._hideInput('district_id');
                }
            }
        });
    },

    _onChangeDistrict: function () {
        if (this.countryCode !== 'VN') {
            return def;
        }
        this._changeDistrict();
    },

    _changeDistrict: function (init = false) {
        const districtId = parseInt(this.addressForm.district_id.value);
        if (!districtId) { return; }
        return rpc(`/shop/ward_info/${districtId}`).then((data) => {
            let selectWards = this.addressForm.ward_id;
            if (!init || selectWards.options.length === 1) {
                if (data.wards.length) {
                    selectWards.options.length = 1;
                    data.wards.forEach((ward) => {
                        let option = new Option(ward[1], ward[0]);
                        option.setAttribute('data-code', ward[2]);
                        selectWards.appendChild(option);
                    });
                    this._showInput('ward_id');
                } else {
                    this._hideInput('ward_id');
                }
            }
        });
    }
})
