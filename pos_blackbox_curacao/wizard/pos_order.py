# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PosOrderPrint(models.TransientModel):
    _name = 'pos.order.print.wizard'
    _description = 'POS Order Print'

    def _default_order(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            order = self.env['pos.order'].browse(active_id)
            return order
        return False

    pos_config_id = fields.Many2one('pos.config', string="POS Counter", required=True)
    pos_order_to_print = fields.Many2one('pos.order', string="POS Order", required=True, default=_default_order)


    def generate_pos_order_nfd(self):
        # Just to Avoid Undefined Error
        # Main Stuff is happening at data_model.js
        pass
