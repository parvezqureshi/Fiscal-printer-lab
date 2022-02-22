# -*- coding: utf-8 -*-
{
    'name': "Blackbox Curacao Module",

    'summary': """
        Fiscal Data Module For Curacao Fiscal Printer""",

    'description': """
This module turn an Odoo Point Of Sale module into a certified Curacao cash register.
It allows the communication on with a certified Fiscal Data Module and will modify the
behaviour of the Point of Sale.

Legal
-----
**The pos_blackbox_curacao sources is only certified Which is sold via Blueback B.V**
An obfuscated and certified version of the pos_blackbox_curacao may be provided on
requests for on-premise installations.
No modified version is certified and supported by Odoo India or Blueback B.V.
    """,

    'author': "Odoo India",
    'website': "http://www.odoo.com",
    'category': 'Point of Sale',
    'version': '1.0',

    'depends': ['base','point_of_sale','pos_discount','pos_reprint'],

    'data': [
        'security/ir.model.access.csv',
        'wizard/pos_order.xml',
        'wizard/z_report.xml',
        'views/templates.xml',
        'views/z_report.xml',
        'views/partner_view.xml',
        'views/pos_config_view.xml',
        'report/pos_order_report.xml',
        'report/pos_order_report_templates.xml',
    ],

    'qweb': [
        'static/src/xml/tax_exempt.xml',
        'static/src/xml/button_templates.xml',
        'static/src/xml/popup.xml',
    ],
}