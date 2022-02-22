odoo.define('pos_blackbox_curacao.popup', function (require) {
    "use strict";

    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var PopupWidget = require('point_of_sale.popups');
    var rpc = require('web.rpc');
    var Session = require('web.Session');

    var _t = core._t;

    var ZReportPopupWidget = PopupWidget.extend({
        template: 'ZReportPopupWidget',
        show: function(options){
            options = options || {};
            var self = this;
            this._super(options);
            this.renderElement();
            $('#report_type').change(function(){
                var report_type = Number($(this).val());
                $(".report_date_picker").hide();
                $(".report_number").hide();
                if(report_type == 1 || report_type == 3){
                    $(".report_date_picker").show();
                }else if(report_type == 2 || report_type == 4){
                    $(".report_number").show();
                }
            });
        },
        click_confirm: function(){
            var self = this;
            var report_type = Number($('#report_type').val());
            if(report_type){
                if(report_type == 1 || report_type == 3){
                    var start_date = $("#start_date").val();
                    var end_date = $("#end_date").val();
                    if (start_date && end_date){
                        if (self.pos.config.proxy_ip) {
                            var param = {
                                'report_type': report_type,
                                'start_date': start_date,
                                'end_date': end_date,
                                'start_z_no': 0,
                                'end_z_no': 0,
                                'com_port': self.pos.config.com_port
                            };
                            var url = "http://"+self.pos.config.proxy_ip;
                            self.connection = new Session(undefined,url, { use_cors: true});
                            self.connection.rpc('/action_extended_z_report',param,{timeout: 15000}).then(function (response) {
                                if (response && response.code != 0) {
                                    self.comand_error(response);
                                }
                            });
                        } else {
                            self.comand_error({'message': 'Receipt Printer Option is not Enable in POS Configuration.'});
                        }
                    }else{
                        return alert(_t("Please select start/end date."));
                    }
                }else if(report_type == 2 || report_type == 4){
                    var start_z_number = $("#start_z_number").val();
                    var end_z_number = $("#end_z_number").val();
                    console.log("report_type...",report_type)
                    if (start_z_number && end_z_number){
                        if (self.pos.config.proxy_ip) {
                            var param = {
                                'report_type': report_type,
                                'start_date': false,
                                'end_date': false,
                                'start_z_no': start_z_number,
                                'end_z_no': end_z_number,
                                'com_port': self.pos.config.com_port
                            };
                            var url = "http://"+self.pos.config.proxy_ip;
                            self.connection = new Session(undefined,url, { use_cors: true});
                            self.connection.rpc('/action_extended_z_report',param,{timeout: 15000}).then(function (response) {
                                self.gui.close_popup();
                                if (response && response.code != 0) {
                                    self.comand_error(response);
                                }
                            });
                        } else {
                            self.comand_error({'message': 'Receipt Printer Option is not Enable in POS Configuration.'});
                        }
                    }else{
                        return alert(_t("Please enter start/end Z-number."));
                    }
                }
            }else{
                return alert(_t("Please Select Report Type."));
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
    gui.define_popup({name:'zreport_popup', widget: ZReportPopupWidget});

});

