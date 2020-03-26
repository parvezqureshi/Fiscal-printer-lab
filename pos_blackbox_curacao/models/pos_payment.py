# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class AccountJournal(models.Model):
    _inherit = 'pos.payment.method'

    fiscal_payment_type = fields.Many2one('fiscal_curacao.payment_method', string="Fiscal Printer Payment Type")

class FiscalPaymentMethod(models.Model):
    _name = 'fiscal_curacao.payment_method'
    _rec_name = 'payment_method_name'

    payment_method_id = fields.Selection([
        ('1', '1'), ('2', '2'), ('3', '3'),
        ('4', '4'), ('5', '5'), ('6', '6'),
        ('7', '7'), ('8', '8'), ('9', '9'),
        ('10', '10'), ('11', '11')],
        string="Payment Method Code", required=True, default='1',
        help="Code Must be between 1-11. Enter the Id of Payment type which has been configured in Fiscal Printer")
    payment_method_name = fields.Char(string="Payment Method", required=True)
