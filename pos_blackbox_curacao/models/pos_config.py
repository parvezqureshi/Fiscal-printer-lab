# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import pytz

from odoo import fields, models, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    cash_register_number = fields.Integer(
        string='Cash Register/Printer Number', help='This Number will be use in reciept for Generating NKF number')

    uplift_product_id = fields.Many2one('product.product', string='Uplift Product',
                                        help="The product used to encode the customer Uplift.")

    service_charge = fields.Float(
        string='Service Charge(%)', help='Service Charge for Invoices')
    service_charge_product_id = fields.Many2one('product.product', string='Service Charge Product',
                                                help="The product used to encode the customer Service Charge.")

    _sql_constraints = [
        ('cash_register_number_validation', 'CHECK (cash_register_number<100)',
         'Cash Register Value must be less than 100!'),
    ]
    proxy_ip = fields.Char(string='IP Address', size=45,
        help='The hostname or ip address of the hardware proxy, Will be autodetected if left empty.')

    com_port = fields.Integer(string='COM Port')
    system_password = fields.Char(
        string='System Password', help='Requires while Setting Permission of COM Port')

    @api.model
    def set_date_time(self):
        tz_name = self.env.context.get('tz') or self.env.user.tz
        if tz_name:
            user_tz = pytz.timezone(tz_name)
            utc = pytz.utc
            dt = user_tz.localize(datetime.datetime.now()).astimezone(utc)
            date = dt.strftime("%d%m%Y")
            time = dt.strftime("%H%M%S")
            return date+"_"+time
        return False

    def set_permission(self):
        # Just to avoid Undefined Error, Main function is Happening at data_model.js
        pass

class Partner(models.Model):
    _inherit = 'res.partner'

    crib = fields.Char(string='CRIB Number')
    is_tax_exempt = fields.Boolean(string='Tax Exempted')
