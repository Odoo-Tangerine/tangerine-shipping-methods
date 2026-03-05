/** @odoo-module */

import { patch } from '@web/core/utils/patch';
import { rpc } from '@web/core/network/rpc';
import { CustomerAddress } from '@portal/interactions/address';

patch(CustomerAddress.prototype, {
    setup() {
        super.setup();
        this.elementState = this.addressForm.state_id;
        this.elementWards = this.addressForm.ward_id;
    },

    _changeOption(selectElement, choices, defaultValue) {
        if (!selectElement) return;
        // empty existing options, only keep the placeholder.
        selectElement.options.length = 1;
        if (choices.length) {
            choices.forEach((item) => {
                const option = new Option(item[1], item[0]);
                option.setAttribute('data-code', item[2]);
                if (defaultValue && item[0] == defaultValue) {
                    option.selected = true;
                }
                selectElement.appendChild(option);
            });
        }
    },

    async _onChangeCountry(init = false) {
        await this.waitFor(super._onChangeCountry(init));
        if (this._getSelectedCountryCode() !== 'VN') {
            this._changeOption(this.elementWards, []);
            this._hideInput('ward_id');
        }
    },

    async onChangeState() {
        await this.waitFor(super.onChangeState());
        if (this._getSelectedCountryCode() !== 'VN') return;
        const stateId = this.elementState.value;
        const currentWardId = this.elementWards ? this.elementWards.value : null;
        let choices = [];
        if (stateId) {
            const data = await this.waitFor(rpc(`/my/address/state_vn_info/${stateId}`, {}));
            choices = data.wards;
        }
        this._changeOption(this.elementWards, choices, currentWardId);
        if (choices.length > 0) {
            this._showInput('ward_id');
        } else {
            this._hideInput('ward_id');
        }
    },
});
