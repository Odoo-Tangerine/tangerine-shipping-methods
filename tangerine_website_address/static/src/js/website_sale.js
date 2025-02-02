/** @odoo-module **/
import { WebsiteSale } from '@website_sale/js/website_sale';
import { debounce } from "@web/core/utils/timing";

WebsiteSale.include({
    events: Object.assign({}, WebsiteSale.prototype.events, {
        'change select[name="district_id"]': '_onChangeDistrict',
    }),

    _changeCountry: function () {
        if (!$("#country_id").val()) { return; }
        return this.rpc("/shop/country_infos/" + $("#country_id").val(), {
            mode: $("#country_id").attr('mode'),
        }).then(function (data) {
            // placeholder phone_code
            $("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');

            // populate states and display
            var selectStates = $("select[name='state_id']");
            // dont reload state at first loading (done in qweb)
            if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
                if (data.states.length || data.state_required) {
                    selectStates.html('');
                    selectStates.append($('<option>').text('State / Province').attr('value', ''));
                    data.states.forEach((x) => {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0])
                            .attr('data-code', x[2]);
                        selectStates.append(opt);
                    });
                    selectStates.parent('div').show();
                } else {
                    selectStates.val('').parent('div').hide();
                }
                selectStates.data('init', 0);
            } else {
                selectStates.data('init', 0);
            }

            // manage fields order / visibility
            if (data.fields) {
                if ($.inArray('zip', data.fields) > $.inArray('city', data.fields)){
                    $(".div_zip").before($(".div_city"));
                } else {
                    $(".div_zip").after($(".div_city"));
                }
                var all_fields = ["street", "zip", "city", "country_name"]; // "state_code"];
                all_fields.forEach((field) => {
                    $(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields)>=0);
                });
            }

            if ($("label[for='zip']").length) {
                $("label[for='zip']").toggleClass('label-optional', !data.zip_required);
                $("label[for='zip']").get(0).toggleAttribute('required', !!data.zip_required);
            }
            if ($("label[for='zip']").length) {
                $("label[for='state_id']").toggleClass('label-optional', !data.state_required);
                $("label[for='state_id']").get(0).toggleAttribute('required', !!data.state_required);
            }
        });
    },

    _onChangeState: function (ev) {
        if (!this.$('.checkout_autoformat').length) {
            return;
        }
        return this._super.apply(this, arguments).then(() => {
            if (!$("select[name='state_id']").val()) { return; }
            return this.rpc("/shop/district_infos/" + $("select[name='state_id']").val(), {
                    mode: $("#country_id").attr('mode'),
                }).then((data) => {
                    var selectDistricts = $("select[name='district_id']");
                    if (selectDistricts.data('init') === 0 || selectDistricts.find('option').length === 1) {
                        if (data.districts.length) {
                            selectDistricts.html('');
                            selectDistricts.append($('<option>').text('District').attr('value', ''));
                            data.districts.forEach((d) => {
                                var opt = $('<option>').text(d[1])
                                    .attr('value', d[0])
                                    .attr('data-code', d[2]);
                                selectDistricts.append(opt);
                            });
                            selectDistricts.parent('div').show();
                        } else {
                            selectDistricts.val('').parent('div').hide();
                        }
                        selectDistricts.data('init', 0);
                    } else {
                        selectDistricts.data('init', 0);
                    }
            });
        });
    },

    _changeDistrict: function () {
        if (!$("select[name='district_id']").val()) { return; }
        return this.rpc("/shop/ward_infos/" + $("select[name='district_id']").val(), {
                mode: $("#country_id").attr('mode'),
            }).then((data) => {
                console.log(data)
                var selectWards = $("select[name='ward_id']");
                if (selectWards.data('init') === 0 || selectWards.find('option').length === 1) {
                    if (data.wards.length) {
                        selectWards.html('');
                        selectWards.append($('<option>').text('Ward').attr('value', ''));
                        data.wards.forEach((w) => {
                            var opt = $('<option>').text(w[1])
                                .attr('value', w[0])
                                .attr('data-code', w[2]);
                            selectWards.append(opt);
                        });
                        selectWards.parent('div').show();
                    } else {
                        selectWards.val('').parent('div').hide();
                    }
                    selectWards.data('init', 0);
                } else {
                    selectWards.data('init', 0);
                }
        });
    },

    _onChangeDistrict: function (ev) {
        if (!this.$('.checkout_autoformat').length) {
            return;
        }
        return this._changeDistrict();
    },
});

