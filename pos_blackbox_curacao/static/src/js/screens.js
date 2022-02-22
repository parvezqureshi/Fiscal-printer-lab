odoo.define('pos_fiscal_curacao.pos_fiscal_curacao', function (require) {
"use strict";

var ajax = require('web.ajax');
var core = require('web.core');
var gui = require('point_of_sale.gui');
var screens = require('point_of_sale.screens');
var devices = require('point_of_sale.devices');
var models = require('point_of_sale.models');
var chrome = require('point_of_sale.chrome');
var PosBaseWidget = require('point_of_sale.BaseWidget');
var rpc = require('web.rpc');
var Session = require('web.Session');


var _t = core._t;

models.load_fields('res.partner','crib');
models.load_fields('res.partner','is_tax_exempt');
models.load_fields('res.partner','is_company');
models.load_fields('pos.payment.method','fiscal_payment_type');

models.load_models({
    model: 'ir.sequence',
    fields: ['number_increment','number_next_actual'],
    loaded: function(self,ir_seq){ self.ir_seq = ir_seq; },
});

models.load_models({
    model: 'fiscal_curacao.payment_method',
    fields: ['payment_method_id','payment_method_name'],
    loaded: function(self, payment_method_list){ self.payment_method_list = payment_method_list; },
});

devices.ProxyDevice.include({
    print_receipt: function(receipt){
        //Overrieding Existing Printing Mechanism
    },
});

// Main fiscal Order Processing and sending Mechanism.
var PaymentScreen = screens.PaymentScreenWidget.extend({
//    validate_order: function(force_validation) {
//        if (this.order_is_valid(force_validation)) {
//            this.orders = this.pos.get_order().export_for_printing();
//            this.client_details = this.pos.get_client();
//            var paymentlines = this.pos.get_order().get_paymentlines();
//            var orderlines = this.pos.get_order().get_orderlines();
//            var order_value = this.pos.get_order();
//            var prom = Promise.resolve();
//            var self = this;
//            _.each(paymentlines, function (payment, index) {
//                var payment_type_id = payment.payment_method.fiscal_payment_type[0];
//                var method = self.pos.payment_method_list.find(function (types) {
//                    return types.payment_method_id == payment_type_id;
//                });
//                var payment_method_id = method && method.payment_method_id || 1;
//                _.extend(self.orders.paymentlines[index], { 'fiscal_payment_type': payment_method_id });
//            });
//            _.each(orderlines, function (order, index) {
//                _.extend(self.orders.orderlines[index], {
//                    'old_price': order.product.lst_price,
//                    'product_id': order.product.id,
//                    'old_tax': self.pos.taxes_by_id[order.product.taxes_id[0]],
//                });
//            });
//            prom.then(function () {
//                self.orders =  _.extend(self.orders, {
//                    client_details: self.client_details,
//                    pos_config: self.pos.config,
//                    is_credit_note: order_value.is_credit_note,
//                    nkf_ref: order_value.nkf_ref,
//                    global_discount_pc: order_value.global_discount_pc,
//                    txn_number: self.generate_txn()
//                });
//                self.orders =  _.extend(self.orders, {
//                    global_discount_product: self.pos.config.discount_product_id ? self.pos.config.discount_product_id[0] : false,
//                    global_tip_product: self.pos.config.tip_product_id ? self.pos.config.tip_product_id[0] : false,
//                    global_uplift_product: self.pos.config.uplift_product_id ? self.pos.config.uplift_product_id[0] : false,
//                    service_charge: self.pos.config.service_charge,
//                    service_charge_product_id: self.pos.config.service_charge_product_id ? self.pos.config.service_charge_product_id[0] : false,
//                    com_port: self.pos.config.com_port,
//                    date_order: order_value.creation_date
//                });
//                self.pos.db.last_order = self.orders;
//                if(self.pos.config.proxy_ip){
//                    self.pos.chrome.loading_show();
//                    self.pos.chrome.loading_message(_t('Printing ...'));
//                    var url = "http://"+self.pos.config.proxy_ip;
//                    self.connection = new Session(undefined,url, { use_cors: true});
//                    self.connection.rpc('/action_validate_payment',self.orders,{timeout: 15000}).then(function (response) {
//                        self.pos.chrome.loading_message(_t('Printing Done...'), 1);
//                        self.pos.chrome.loading_hide();
//                        if (response && response.code) {
//                           return self.comand_error(response);
//                        } else {
//                            self.finalize_validation();
//                        }
//                    });
//                } else {
//                    return self.comand_error({"message": "Reciept Printer is not enable in Setting"});
//                }
//            });
//        }
//    },
    generate_txn: function () {
        var self = this;
        var ir_seq = _.filter(this.pos.ir_seq, function(sequence) {
            return sequence.id == self.pos.config.sequence_id[0];
        });
        var order_number = String(ir_seq[0].number_next_actual);
        ir_seq[0].number_next_actual = parseInt(ir_seq[0].number_next_actual) + parseInt(ir_seq[0].number_increment);
        return ("000000" + order_number).slice(-6);
    },
    comand_error: function (error) {
        this.gui.show_popup('error',{
            'title': _t('Fiscal Printer Comand Error'),
            'body': _t(
                'Error Code : '+ error.code + ' ' +
                'Error Message:' + error.message
            ),
        });
        return false;
    },
});
gui.define_screen({name:'payment', widget: PaymentScreen});

/*
*   [Tax Exemption]
*   Adding Tax Exemption Option to customer. Implementing 2 new field on POS and Backend Module.
*   1. is_tax_exempt : Boolean Filed to set on customer if this customer is Exempted for Tax or not
*   2. CRIB: Madatory info field on Tax Exempted customer.
*   3. Is_comapny: for Fiscal Credit Right Conditions
*   - Inherting Widget to Support Boolean Filed storage (Checkbox) and Checking Condition for CRIB.
*/
var ClientListScreenWidget = screens.ClientListScreenWidget.extend({
    save_client_details: function(partner) {
        var self = this;

        var fields = {};

        /*
        * Custom Code
        */
        if ((fields.is_tax_exempt || fields.is_company) && !fields.crib) {
            this.gui.show_popup('error',{
                title:_t('Validation Error'),
                body:_t('A Customer CRIB Is Required When Tax Exemption or Is Company is Enable'),
            });
            return;
        }
        /*
        * Super Function
        */
        this.$('.client-details-contents .detail').each(function(idx,el){
            if (el.name == 'is_company')
            if (self.integer_client_details.includes(el.name)){
                var parsed_value = parseInt(el.value, 10);
                if (isNaN(parsed_value)){
                    fields[el.name] = false;
                }
                else{
                    fields[el.name] = parsed_value
                }
            }
            /* Custom Code */
            else if(el.type === "checkbox"){
                fields[el.name] = $(el).is(':checked');
            }
            /* ======================= */
            else{
                fields[el.name] = el.value || false;
            }
        });

        if (!fields.name) {
            this.gui.show_popup('error',_t('A Customer Name Is Required'));
            return;
        }

        if (this.uploaded_picture) {
            fields.image_1920 = this.uploaded_picture;
        }

        fields.id = partner.id || false;

        var contents = this.$(".client-details-contents");
        contents.off("click", ".button.save");


        rpc.query({
                model: 'res.partner',
                method: 'create_from_ui',
                args: [fields],
        }).then(function(partner_id){
            self.saved_client_details(partner_id);
        }).catch(function(error){
            error.event.preventDefault();
            var error_body = _t('Your Internet connection is probably down.');
            if (error.message.data) {
                var except = error.message.data;
                error_body = except.arguments && except.arguments[0] || except.message || error_body;
            }
            self.gui.show_popup('error',{
                'title': _t('Error: Could not Save Changes'),
                'body': error_body,
            });
            contents.on('click','.button.save',function(){ self.save_client_details(partner); });
        });
    },
});
gui.define_screen({name:'clientlist', widget: ClientListScreenWidget});

/*
*   Implementation logic for,
*   If Credit Note Button is selected, all product item quantity should be less than zero.
*
*/
screens.ActionpadWidget.include({
    renderElement: function() {
        this._super();
        var self = this;
        this.$('.pay').click(function () {
            var order = self.pos.get_order();
            var client_details = self.pos.get_client();
            var is_service_charge_active = self.pos.config.service_charge > 0 ? true : false;
            var valid_service_charge = !is_service_charge_active;
            var has_valid_product_lot = _.every(order.orderlines.models, function(line){
                return line.has_valid_product_lot();
            });
            order.is_credit_note = false;
            if (is_service_charge_active) {
                _.each(self.pos.get_order().get_orderlines(), function(line) {
                    if (line.product.id === self.pos.config.service_charge_product_id[0]) {
                        valid_service_charge = true;
                    }
                });
            }
            var valid_order = true;
            if (self.__parentedParent.$el.find('.js_creditNoteBtn').hasClass('credit_note_mode')) {
                _.each(self.pos.get_order().get_orderlines(), function(line) {
                    if (line.quantity >= 0) {
                        valid_order = false;
                        return false;
                    }
                });
                order.is_credit_note = true;
            }
            if(!valid_order) {
                self.gui.show_screen('products');
                self.gui.show_popup('error',{
                    'title': _t('Invalid Item Quantity'),
                    'body':  _t('All products must have quantity less than zero in case of Credit Note'),
                });
            }
            else if (!valid_service_charge) {
                self.gui.show_screen('products');
                self.gui.show_popup('error',{
                    'title': _t('Service Charge Not Applied !'),
                    'body':  _t('Service Charge is configured in setting but you have not applied it here!'),
                });
            }
            else if (!has_valid_product_lot) {
                self.gui.show_popup('confirm',{
                    'title': _t('Empty Serial/Lot Number'),
                    'body':  _t('One or more product(s) required serial/lot number.'),
                    confirm: function(){
                        self.gui.show_screen('payment');
                    },
                });
            }
            else if (client_details && client_details.is_company && !client_details.crib) {
                self.gui.show_screen('products');
                self.gui.show_popup('error',{
                    'title': _t('CRIB Number Not Found'),
                    'body':  _t('CRIB Number is Must require When Company is selected.'),
                });
            } else {
                self.gui.show_screen('payment');
            }
        });
    }
});

//For Reseting credit Note Button after order is completed.

var ReceiptScreenWidget = screens.ReceiptScreenWidget.extend({
    click_next: function() {
        this._super();
        this.__parentedParent.$el.find('.credit_note_mode').removeClass('credit_note_mode');
    },
});
gui.define_screen({name:'receipt', widget: ReceiptScreenWidget});


var XreportButton = PosBaseWidget.extend({
    template: 'XreportButton',
    start: function(){
        var self = this;
        this.$el.click(function(){
            self.gui.show_popup('confirm',{
                'title': _t('Print X-Report'),
                'body':  _t('Are you sure you want to print X-Report ?'),
                confirm: function(){
                    if (self.pos.config.proxy_ip) {
                        self.param = {};
                        self.param['com_port'] = self.pos.config.com_port;
                        var url = "http://"+self.pos.config.proxy_ip;
                        self.connection = new Session(undefined,url, { use_cors: true});
                        self.connection.rpc('/action_x_report',self.param,{timeout: 15000}).then(function (response) {
                            if (response && response.code != 0) {
                                self.comand_error(response);
                            }
                        });
                    } else {
                        self.comand_error({'message': 'Receipt Printer Option is not Enable in POS Configuration.'});
                    }
                },
            });
        });
    },
    comand_error: function (error) {
        this.gui.show_popup('error',{
            'title': _t('Fiscal Printer Comand Error'),
            'body': _t(
                'Error Code : '+ error.code + ' ' +
                'Error Message:' + error.message
            ),
        });
        return false;
    },
});

var ZreportButton = PosBaseWidget.extend({
    template: 'ZreportButton',
    start: function(){
        var self = this;
        this.$el.click(function(){
            self.gui.show_popup('zreport_popup',{});
        });
    },
    comand_error: function (error) {
        this.gui.show_popup('error',{
            'title': _t('Fiscal Printer Comand Error'),
            'body': _t(
                'Error Code : '+ error.code + ' ' +
                'Error Message:' + error.message
            ),
        });
        return false;
    },
});

chrome.Chrome.include({
    build_widgets: function () {
        var proxy_status_index = _.findIndex(this.widgets, function (widget) {
            return widget.name === "proxy_status";
        });
        this.widgets.splice(proxy_status_index, 0, {
            'name':   'xreport',
            'widget': XreportButton,
            'append':  '.pos-rightheader',
        });
        this.widgets.splice(proxy_status_index, 0, {
            'name':   'zreport',
            'widget': ZreportButton,
            'append':  '.pos-rightheader',
        });
        
        this._super();
    },
});

// Implentation of Uplif Button
var UpliftButton = screens.ActionButtonWidget.extend({
    template: 'UpliftButton',
    button_click: function(){
        var self = this;
        this.gui.show_popup('number',{
            'title': 'Uplift Amount',
            'value': 0,
            'confirm': function(val) {
                self.apply_uplift(val);
            },
        });
    },
    apply_uplift: function(pc) {
        var order    = this.pos.get_order();
        var lines    = order.get_orderlines();
        var product  = this.pos.db.get_product_by_id(this.pos.config.uplift_product_id[0]);

        // Remove existing uplift
        var i = 0;
        while ( i < lines.length ) {
            if (lines[i].get_product() === product) {
                order.remove_orderline(lines[i]);
            } else {
                i++;
            }
        }

        order.add_product(product, { price: pc });
    },
});

screens.define_action_button({
    'name': 'uplift',
    'widget': UpliftButton,
    'condition': function(){
        return this.pos.config.uplift_product_id;
    },
});

// Implementation of Service Charge Button
var ServiceChargeButton = screens.ActionButtonWidget.extend({
    template: 'ServiceChargeButton',
    button_click: function(){
        var val = Math.round(Math.max(0,Math.min(100, this.pos.config.service_charge)));
        this.apply_serviceCharge(val);
    },
    apply_serviceCharge: function(pc) {
        var order    = this.pos.get_order();
        var lines    = order.get_orderlines();
        var product  = this.pos.db.get_product_by_id(this.pos.config.service_charge_product_id[0]);

        // Remove existing service_charges
        var i = 0;
        while ( i < lines.length ) {
            if (lines[i].get_product() === product) {
                order.remove_orderline(lines[i]);
            } else {
                i++;
            }
        }

        // Add service_charge
        var service_charge = pc / 100.0 * order.get_total_with_tax();

        if( service_charge > 0 ){
            order.add_product(product, { price: service_charge });
        }
    },
});

screens.define_action_button({
    'name': 'service_charge',
    'widget': ServiceChargeButton,
    'condition': function(){
        return this.pos.config.service_charge > 0 && this.pos.config.service_charge_product_id;
    },
});

// Overrideing Discount for adding Discount Persentage into Orderline.
var DiscountButton = screens.ActionButtonWidget.extend({
    template: 'DiscountButton',
    button_click: function(){
        var self = this;
        this.gui.show_popup('number',{
            'title': 'Discount Percentage',
            'value': this.pos.config.discount_pc,
            'confirm': function(val) {
                val = Math.round(Math.max(0,Math.min(100,val)));
                self.apply_discount(val);
            },
        });
    },
    apply_discount: function(pc) {
        var order    = this.pos.get_order();
        var lines    = order.get_orderlines();
        var product  = this.pos.db.get_product_by_id(this.pos.config.discount_product_id[0]);

        // Remove existing discounts
        var i = 0;
        while ( i < lines.length ) {
            if (lines[i].get_product() === product) {
                order.remove_orderline(lines[i]);
            } else {
                i++;
            }
        }

        // Add discount
        var discount = - pc / 100.0 * order.get_total_with_tax();

        if( discount < 0 ){
            order.add_product(product, { price: discount });
            order.global_discount_pc = pc;
            this.pos.set_order(order);
        }
    },
});


var ReprintButton = screens.ActionButtonWidget.extend({
    template: 'ReprintButton',
    button_click: function() {
        if (this.pos.db.last_order) {
            var url = "http://"+this.pos.config.proxy_ip;
            this.connection = new Session(undefined,url, { use_cors: true});
            var self = this;
            this.connection.rpc('/action_generate_pos_order_nfd',this.pos.db.last_order,{timeout:15000}).then(function(response) {
                if (response && response.code) {
                    self.comand_error(response);
                }
            });
        } else {
            this.gui.show_popup('error', {
                'title': _t('Nothing to Print'),
                'body':  _t('There is no previous receipt to print.'),
            });
        }
    },
    comand_error: function (error) {
        this.gui.show_popup('error',{
            'title': _t('Fiscal Printer Comand Error'),
            'body': _t(
                'Error Code : '+ error.code + ' ' +
                'Error Message:' + error.message
            ),
        });
        return false;
    },
});

screens.ProductScreenWidget.include({
    start: function(){
        var test = this._super.apply(this, arguments);
        if (this.action_buttons.discount){
            this.action_buttons.discount.destroy();
            delete this.action_buttons.discount;

            var widget = new DiscountButton(this,{});
            widget.appendTo(this.$('.control-buttons'));
            this.action_buttons['discount'] = widget;
        }
        if (this.action_buttons.reprint){
            this.action_buttons.reprint.destroy();
            delete this.action_buttons.reprint;

            var widget = new ReprintButton(this,{});
            widget.appendTo(this.$('.control-buttons'));
            this.action_buttons['reprint'] = widget;
        }
        return test;
    }

});

var PermissionButton = PosBaseWidget.extend({
    template: 'permission_button',
    start: function(){
        var self = this;
        this.$el.click(function () {
            if (self.pos.config.proxy_ip) {
                self.params = {};
                var url = "http://" + self.pos.config.proxy_ip;
                ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                    model: 'pos.config',
                    method: 'search_read',
                    args: [[['id', '=', self.pos.config.id]]],
                    kwargs: {}
                }).then(function(pos_config){
                    self.params['password'] = pos_config[0].system_password;
                    self.connection = new Session(undefined,url, { use_cors: true});
                    self.connection.rpc('/action_set_permission',self.params,{timeout: 15000}).then(function (response) {
                        if (!response.error) {
                            self.$('i.fa.fa-fw').removeClass('fa-lock').addClass('fa-unlock')
                        } else {
                            self.$('i.fa.fa-fw').removeClass('fa-unlock').addClass('fa-lock');
                            self.show_error(_t('Access Error'), response.error);
                        }
                    }).catch(function (error) {
                        self.show_error(_t('Connection Error'), error.message.code);
                    });

                });
            } else {
                self.show_error(_t('Configuration Error'), error_code);
            }
        });
    },
    show_error: function (title, error_code) {
        this.gui.show_popup('error',{
            'title': title,
            'body': _t('Error : '+ error_code),
        });
    },
});


chrome.Chrome.include({
    build_widgets: function () {
        var proxy_status_index = _.findIndex(this.widgets, function (widget) {
            return widget.name === "proxy_status";
        });
        this.widgets.splice(proxy_status_index, 0, {
            'name':   'permission_button',
            'widget': PermissionButton,
            'append':  '.pos-rightheader',
        });
        this._super();
    },
});


});
