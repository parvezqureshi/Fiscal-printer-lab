# -*- coding: utf-8 -*-

import ctypes
import logging
import math

from odoo import http, _
from ctypes import byref, c_int, c_char
from odoo.modules.module import get_module_resource
from .. escpos.constants import *
from .. escpos.error_code import get_error_message

_logger = logging.getLogger(__name__)

class nfd(http.Controller):

    @http.route(['/action_generate_pos_order_nfd'], type='json', auth="none", cors='*')
    def print_receipt_body(self, **receipt):

        def check(string):
            return string != True and bool(string) and string.strip()

        def price(amount):
            return ("{0:."+str(receipt['precision']['price'])+"f}").format(amount)

        def money(amount):
            return ("{0:."+str(receipt['precision']['money'])+"f}").format(amount)

        def quantity(amount):
            if math.floor(amount) != amount:
                return ("{0:."+str(receipt['precision']['quantity'])+"f}").format(amount)
            else:
                return str(amount)

        def printline(left, right='', width=50, ratio=0.5, indent=0):
            lwidth = int(width * ratio)
            rwidth = width - lwidth
            lwidth = lwidth - indent

            left = left[:lwidth]
            if len(left) != lwidth:
                left = left + ' ' * (lwidth - len(left))

            right = right[-rwidth:]
            if len(right) != rwidth:
                right = ' ' * (rwidth - len(right)) + right

            return ' ' * indent + left + right

        def print_taxes():
            taxes = receipt['tax_details']
            for tax in taxes:
                eprint(printline(tax['name'],price(tax['amount']), width=50,ratio=0.6))

        def eprint(text):
            self.Handle_EpsonFiscalDriver.AddDataField(bytes(NFD_PRINT, 'utf-8'), 2)
            self.Handle_EpsonFiscalDriver.AddDataField(bytes("", 'utf-8'), 2)
            self.Handle_EpsonFiscalDriver.AddDataField(bytes(text, 'utf-8'), len(str(text)))
            send_command()

        def nfd_open():
            self.Handle_EpsonFiscalDriver.AddDataField(bytes(NFD_OPN_RECPT, 'utf-8'), 2)
            self.Handle_EpsonFiscalDriver.AddDataField(bytes("\x00\x00", 'utf-8'), 2)
            send_command()

        def nfd_close():
            self.Handle_EpsonFiscalDriver.AddDataField(bytes(NFD_CLOSE, 'utf-8'), 2)
            self.Handle_EpsonFiscalDriver.AddDataField(bytes("\x00\x00", 'utf-8'), 2)
            send_command()

        def send_command():
            self.Handle_EpsonFiscalDriver.SendCommand()
            if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                self.Handle_EpsonFiscalDriver.AddDataField(bytes(NFD_CLOSE, 'utf-8'), 2)
                self.Handle_EpsonFiscalDriver.AddDataField(bytes("\x00\x00", 'utf-8'), 2)
                self.Handle_EpsonFiscalDriver.SendCommand()

                raise Exception(self.Handle_EpsonFiscalDriver.getReturnCode())

        # Connection
        try:
            _logger.info('Printing Non Fiscal Document')
            path = get_module_resource('hw_blackbox_curacao', 'escpos', 'lib', 'libEpsonFiscalDriver.so')
            self.Handle_EpsonFiscalDriver = ctypes.cdll.LoadLibrary(path)
            Protocol = 1
            self.Handle_EpsonFiscalDriver.setProtocolType(Protocol)
            self.Handle_EpsonFiscalDriver.setComPort(1)
            self.Handle_EpsonFiscalDriver.setBaudRate(9600)
        except:
            _logger.error('Odoo module pos_fiscal_curacao depends on the libEpsonFiscalDriver.so module')

        try:
            self.Handle_EpsonFiscalDriver.OpenPort()
            if ( self.Handle_EpsonFiscalDriver.getLastError() ):
                raise Exception(self.Handle_EpsonFiscalDriver.getLastError())
            nfd_open()
            eprint('               ----------------------')
            if int(receipt['total_with_tax']) < 0:

                eprint('                  Copy Credit Note')
            else:
                eprint('                   Copy Receipt')

            eprint('               ----------------------')
            eprint(' ')

            eprint(receipt['company']['name'])

            if check(receipt['company']['contact_address']):
                eprint(receipt['company']['contact_address'] )
            if check(receipt['company']['phone']):
                eprint('Tel:' + receipt['company']['phone'])
            if check(receipt['company']['vat']):
                eprint('VAT:' + receipt['company']['vat'])
            if check(receipt['company']['email']):
                eprint(receipt['company']['email'])
            if check(receipt['company']['website']):
                eprint(receipt['company']['website'])
            if check(receipt['header']):
                eprint(receipt['header'])
            if check(receipt['cashier']):
                eprint('Served by '+receipt['cashier'])

            eprint(' ')
            eprint(' ')

            # Orderlines
            for line in receipt['orderlines']:
                pricestr = price(line['price_display'])
                if line['discount'] == 0 and line['unit_name'] == 'Unit(s)' and line['quantity'] == 1:
                    eprint(printline(line['product_name'],pricestr,ratio=0.6))
                else:
                    eprint(printline(line['product_name'],ratio=0.6))
                    if line['discount'] != 0:
                        eprint(printline('Discount: '+str(line['discount'])+'%', ratio=0.6, indent=2))
                    if line['unit_name'] == 'Unit(s)':
                        eprint( printline( quantity(line['quantity']) + ' x ' + price(line['price']), pricestr, ratio=0.6, indent=2))
                    else:
                        eprint( printline( quantity(line['quantity']) + line['unit_name'] + ' x ' + price(line['price']), pricestr, ratio=0.6, indent=2))

            # Subtotal if the taxes are not included
            taxincluded = True
            if money(receipt['subtotal']) != money(receipt['total_with_tax']):
                eprint(printline('','-------'));
                eprint(printline(_('Subtotal'),money(receipt['subtotal']),width=50, ratio=0.6))
                print_taxes()
                #eprint(printline(_('Taxes'),money(receipt['total_tax']),width=50, ratio=0.6))
                taxincluded = False


            # Total
            eprint(printline('','-------'));
            eprint(printline(_('         TOTAL'),money(receipt['total_with_tax']),width=50, ratio=0.6))

            eprint(' ')
            eprint(' ')
            # Paymentlines
            for line in receipt['paymentlines']:
                eprint(printline(line['payment_method'], money(line['amount']), ratio=0.6))
            eprint(' ')

            eprint(printline(_('        CHANGE'),money(receipt['change']),width=50, ratio=0.6))
            eprint(' ')

            # Extra Payment info
            if receipt['total_discount'] != 0:
                eprint(printline(_('Discounts'),money(receipt['total_discount']),width=50, ratio=0.6))
            if taxincluded:
                print_taxes()

            # Footer
            if check(receipt['footer']):
                eprint(receipt['footer'])
                eprint(' ')
                eprint(' ')
            eprint(receipt['name'])
            eprint(str(receipt['date_order']))

            return True
        except Exception as e:
            _logger.error('Error While Printing Non Fiscal Document:',e.args)
            return {
                "message": get_error_message(e.args[0]),
                "code": e.args
            }
        finally:
            nfd_close()
            self.Handle_EpsonFiscalDriver.ClosePort()
