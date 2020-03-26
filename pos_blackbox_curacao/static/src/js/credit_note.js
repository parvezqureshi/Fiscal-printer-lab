odoo.define('pos_blackbox_curacao.credit_note', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var core = require('web.core');
var _t = core._t;


var CreditNoteButton = screens.ActionButtonWidget.extend({
    template: 'CreditNoteButton',
    button_click: function(el){
        var self = this;
        this.gui.show_popup('textinput',{
            'title': 'NKF Reference',
            'value': self.pos.get_order().nkf_ref,
            'confirm': function(nkf) {
                var order = self.pos.get_order();
                if (nkf!='') {
                    if (nkf.length === 19) {
                        self.$el.addClass('credit_note_mode');
                        order.is_credit_note = true;
                        order.nkf_ref = nkf;
                    } else {
                        self.gui.show_popup('error',{
                            'title': _t('Invalid NKF Reference length'),
                            'body': _t('Invalid NKF Reference length. Please enter NKF of length 19.'),
                        });
                    }
                } else {
                    self.$el.removeClass('credit_note_mode');
                    order.is_credit_note = false;
                    order.nkf_ref = 0;
                }
                self.pos.set_order(order);
            },
        });
    },
});

screens.define_action_button({
    'name': 'creditNoteButton',
    'widget': CreditNoteButton,
});

});
