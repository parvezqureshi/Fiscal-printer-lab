odoo.define('pos_blackbox_curacao.DataModel', function (require) {
"use strict";

var ajax = require('web.ajax');
var Dialog = require('web.Dialog');
var core = require('web.core');
var Session = require('web.Session');
var ActionManager = require('web.ActionManager');
var Context = require('web.Context');
var _t = core._t;


ActionManager.include({
    _onExecuteAction: function (ev) {
        var def = [];
        this.params = {};
        this.action_name = undefined;
        var self = this;

        var actionData = ev.data.action_data;
        var env = ev.data.env;
        var context = new Context(env.context, actionData.context || {});
        var recordID = env.currentID || null; // pyUtils handles null value, not undefined

        if (actionData.type === 'object') {

            var args = recordID ? [[recordID]] : [env.resIDs];
            if (actionData.args) {
                try {
                    // warning: quotes and double quotes problem due to json and xml clash
                    // maybe we should force escaping in xml or do a better parse of the args array
                    var additionalArgs = JSON.parse(actionData.args.replace(/'/g, '"'));
                    args = args.concat(additionalArgs);
                } catch (e) {
                    console.error("Could not JSON.parse arguments", actionData.args);
                }
            }
            args.push(context.eval());

            var method = actionData.name;

            if (method === 'action_pos_session_closing_control') {
                this.action_name = "/action_z_closure";
                this.proxy_ip = "";
                def.push(new Promise(function (resolve, reject){
                    ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                        model: env.model,
                        method: 'search_read',
                        args: [[['id', '=', args[0][0]]]],
                        kwargs: {}
                    }).then(function(pos_session){
                        ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                            model: 'pos.config',
                            method: 'search_read',
                            args: [[['id', '=', pos_session[0].config_id[0]]]],
                            kwargs: {}
                        }).then(function(pos_config){
                            self.proxy_ip = pos_config[0].proxy_ip;
                            self.params['com_port'] = pos_config[0].com_port;
                            resolve();
                        });
                    });
                }));
            }
            if (method === 'open_session_cb') {
                this.action_name = "/action_set_date_time";
                this.proxy_ip = "";
                def.push(new Promise(function (resolve, reject){
                    ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                    model: env.model,
                    method: 'search_read',
                    args: [[['id', '=', args[0][0]]]],
                    kwargs: {}
                    }).then(function(pos_config){
                        self.proxy_ip = pos_config[0].proxy_ip;
                        self.params['com_port'] = pos_config[0].com_port;
                        resolve();
                    })
                }));
                def.push(new Promise(function (resolve, reject){
                    ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                        model: env.model,
                        method: 'set_date_time',
                        args: [],
                        kwargs: {}
                    }).then(function(dateTime){
                        self.params['date_time'] = dateTime;
                        resolve();
                    })
                }));
            }
            if (method === 'set_permission') {
                this.action_name = "/action_set_permission";
                this.proxy_ip = "";
                def.push(new Promise(function (resolve, reject){
                    ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                        model: env.model,
                        method: 'search_read',
                        args: [[['id', '=', args[0][0]]]],
                        kwargs: {}
                    }).then(function(pos_config){
                        self.proxy_ip = pos_config[0].proxy_ip;
                        self.params['password'] = pos_config[0].system_password;
                        resolve();
                    })
                }));

            }
            if (method === 'generate_zreport') {
                this.action_name = "/action_extended_z_report";
                this.proxy_ip = "";
                def.push(new Promise(function (resolve, reject){
                    ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                        model: env.model,
                        method: 'search_read',
                        args: [[['id', '=', args[0][0]]]],
                        kwargs: {}
                    }).then(function(zreport){
                        zreport = zreport[0];
                        self.params['report_type'] = zreport.report_type;
                        self.params['start_date'] = zreport.start_date;
                        self.params['end_date'] = zreport.end_date;
                        self.params['start_z_no'] = zreport.start_z_no;
                        self.params['end_z_no'] = zreport.end_z_no;

                        ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                            model: 'pos.config',
                            method: 'search_read',
                            args: [[['id', '=', zreport.pos_config_id[0]]]],
                            kwargs: {}
                        }).then(function(pos_config){
                            self.proxy_ip = pos_config[0].proxy_ip;
                            self.params['com_port'] = pos_config[0].com_port;
                            resolve();
                        });
                    });
                }));
            }
            if (method === 'generate_pos_order_nfd') {
                this.action_name = "/action_generate_pos_order_nfd";
                this.proxy_ip = "";

                def.push(new Promise(function (resolve, reject){
                    ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                        model: env.model,
                        method: 'search_read',
                        args: [[['id', '=', args[0][0]]]],
                        kwargs: {}
                    }).then(function(order_wizard){
                        ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                            model: 'pos.order',
                            method: 'get_json_receipt',
                            args: [order_wizard[0].pos_config_id[0], order_wizard[0].pos_order_to_print[0]],
                            kwargs: {}
                        }).then(function(receipt){
                            self.proxy_ip = receipt['proxy_ip'];
                            self.params = receipt;
                            resolve();
                        });
                    });
                }));
            }

            Promise.all(def).then(function () {
                if (self.proxy_ip) {
                    var url = 'http://' + self.proxy_ip;
                    self.connection = new Session(undefined,url, { use_cors: true});
                    self.connection.rpc(self.action_name,self.params,{timeout: 15000}).then(function (return_code) {
                        if (return_code != 0) {
                            alert('Error While Printing Document ',return_code);
                            console.error(_t('Error Code: While Printing one of the following Document : Z Closure, X Report, Set Date Time, Set Perminssion, POS Order NFD.'));
                        }
                    });
                } else if (self.action_name) {
                    Dialog.confirm(self, _t("[Error]: Can not Print Z Closure, X Report and Set Date Time as Hardware Proxy IP is not set in POS Configuration."));
                    console.error(_t('Can not Print Z Closure, X Report and Set Date Time as Hardware Proxy IP is not set in POS Configuration.'));
                }
            });
        }
        return this._super.apply(this, arguments);
    },

});
});
