# -*- coding: utf-8 -*-

import logging
import re
import datetime
import ctypes
import subprocess

from odoo import http
from odoo import models, fields, api, _
from odoo.modules.module import get_module_resource
from .. escpos.constants import *

_logger = logging.getLogger(__name__)


class hw_blackbox_curacao(http.Controller):

    @http.route(['/action_validate_payment'], type='json', auth="none", cors='*')
    def validate_payment(self, **orders):
        self.init_fiscal_driver(orders.get('com_port'))

        try:
            self.Handle_EpsonFiscalDriver.OpenPort()
            if (self.Handle_EpsonFiscalDriver.getLastError()):
                return self.Handle_EpsonFiscalDriver.getLastError()
            # Purge
            self.Handle_EpsonFiscalDriver.Purge()

            if(self.Handle_EpsonFiscalDriver.getProtocolType() == 1):

                self.pos_config = orders.get('pos_config')
                self.client_details = orders.get('client_details')
                self.is_credit_note = orders.get('is_credit_note')
                self.txn_number = orders.get('txn_number')
                self.client_is_company = self.client_details.get(
                    'is_company') if self.client_details else False

                if self.client_is_company:
                    TXN_OPN_RECPT_EXT = "\x00\x01"
                    reciept_type = 2
                else:
                    TXN_OPN_RECPT_EXT = "\x00\x00"
                    reciept_type = 1

                client_name = client_crib = ""
                nkf_ref = ""

                # 1 Open Reciept
                if self.is_credit_note:
                    nkf_ref = orders.get('nkf_ref')
                    if self.client_is_company:
                        TXN_OPN_RECPT_EXT = "\x00\x03"
                        reciept_type = 4
                    else:
                        TXN_OPN_RECPT_EXT = "\x00\x02"
                        reciept_type = 3
                if self.client_details:
                    client_name = self.client_details.get('name') or ""
                    client_crib = self.client_details.get('crib') or ""
                    client_is_tax_exempt = self.client_details.get(
                        'is_tax_exempt') or False

                    if client_is_tax_exempt:
                        if self.is_credit_note:
                            if self.client_is_company:
                                TXN_OPN_RECPT_EXT = "\x00\x07"
                                reciept_type = 4
                            else:
                                TXN_OPN_RECPT_EXT = "\x00\x06"
                                reciept_type = 3
                        else:
                            if self.client_is_company:
                                TXN_OPN_RECPT_EXT = "\x00\x05"
                                reciept_type = 2
                            else:
                                TXN_OPN_RECPT_EXT = "\x00\x04"
                                reciept_type = 1

                nkf = self.make_nkf(orders.get('company').get('vat'), self.pos_config.get(
                    'cash_register_number'), reciept_type, self.txn_number)
                self.create_command(TXN_OPN_RECPT, TXN_OPN_RECPT_EXT, "1", "0", "0001", "0001", str(
                    nkf), str(client_name), str(client_crib), str(nkf_ref))
                self.Handle_EpsonFiscalDriver.SendCommand()

                if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                    raise Exception(
                        self.Handle_EpsonFiscalDriver.getReturnCode())
                self.global_discount_price = 0
                self.global_discount_pc = 0
                self.global_tip_price = 0
                self.global_uplift_price = 0
                self.service_charge = 0

                for order in orders.get('orderlines'):
                    # 2 Add Items to Invoice
                    item_name = str(order.get('product_name'))
                    item_id = order.get('product_id')
                    item_qty = self._format_value(
                        5, 3, abs(order.get('quantity')))
                    item_price = 0
                    if self.client_details and self.client_details.get('is_tax_exempt'):
                        item_price = self._format_value(
                            7, 2, abs(order.get('old_price')))
                    else:
                        item_price = self._format_value(
                            7, 2, abs(order.get('price')))

                    discount_price = self._format_value(
                        7, 2, (abs(order.get('price')) * abs(order.get('discount')) / 100.00))
                    item_tax = self._format_value(2, 2, order.get(
                        'old_tax').get('amount') if order.get('old_tax') else 0)

                    if orders.get("global_discount_product") and item_id == orders.get("global_discount_product"):
                        self.global_discount_price = self._format_value(
                            9, 2, (-1*order.get('price')))
                        self.global_discount_pc = orders.get(
                            'global_discount_pc')
                        continue
                    elif orders.get("global_tip_product") and item_id == orders.get("global_tip_product"):
                        self.global_tip_price = self._format_value(
                            9, 2, (order.get('price')))
                        continue
                    elif orders.get("global_uplift_product") and item_id == orders.get("global_uplift_product"):
                        self.global_uplift_price = self._format_value(
                            9, 2, (order.get('price')))
                        continue
                    elif orders.get("service_charge") and item_id == orders.get("service_charge_product_id"):
                        self.service_charge = self._format_value(
                            9, 2, (order.get('price')))
                        continue
                    else:
                        disc_desc = ""
                        self.create_command(TXN_ADD_ITEM, "\x00\x00", disc_desc, "", "",
                                            "", "", "", "", "", "", item_name, item_qty, item_price, item_tax)

                        # Send Command
                        self.Handle_EpsonFiscalDriver.SendCommand()
                        if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                            raise Exception(
                                self.Handle_EpsonFiscalDriver.getReturnCode())

                        if order.get('discount'):
                            disc_desc = "%s%s" % (order.get('discount'), '%')
                            self.create_command(TXN_ADD_ITEM, "\x00\x02", "", "", "", "", "",
                                                "", "", "", "", disc_desc, item_qty, discount_price, item_tax)

                            # Send Command
                            self.Handle_EpsonFiscalDriver.SendCommand()
                            if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                                raise Exception(
                                    self.Handle_EpsonFiscalDriver.getReturnCode())

                # 3 Add Subtotal
                self.create_command(TXN_SUB_TOT, "\x00\x00")
                self.Handle_EpsonFiscalDriver.SendCommand()
                if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                    raise Exception(
                        self.Handle_EpsonFiscalDriver.getReturnCode())

                # 4 Add Discount
                if self.global_discount_price:
                    self.create_command(TXN_DISCOUNT, "\x00\x00", "Discount "+str(
                        self.global_discount_pc)+"%", self.global_discount_price)
                    self.Handle_EpsonFiscalDriver.SendCommand()
                    if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                        raise Exception(
                            self.Handle_EpsonFiscalDriver.getReturnCode())

                # 5 Add Uplift
                if self.global_uplift_price:
                    self.create_command(
                        TXN_DISCOUNT, "\x00\x01", "Uplift", self.global_uplift_price)
                    self.Handle_EpsonFiscalDriver.SendCommand()
                    if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                        raise Exception(
                            self.Handle_EpsonFiscalDriver.getReturnCode())

                # 6 Add Service Charge
                if self.service_charge:
                    self.create_command(TXN_SER_CHRG, "", self.service_charge)
                    self.Handle_EpsonFiscalDriver.SendCommand()
                    if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                        raise Exception(
                            self.Handle_EpsonFiscalDriver.getReturnCode())

                # 7 Add Payment
                if not self.is_credit_note:
                    for payment in orders.get('paymentlines'):
                        total_paid = self._format_value(
                            9, 2, payment['amount'])
                        self.create_command(TXN_PAYMENT, "\x00\x00", str(
                            payment.get('fiscal_payment_type', 1)), total_paid, "", "", "")
                        self.Handle_EpsonFiscalDriver.SendCommand()
                        if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                            raise Exception(
                                self.Handle_EpsonFiscalDriver.getReturnCode())

                    # 6 Add Donation/Tip
                    if self.global_tip_price:
                        self.create_command(
                            TXN_TIP, "\x00\x00", "Tip", self.global_tip_price)
                        self.Handle_EpsonFiscalDriver.SendCommand()
                        if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                            raise Exception(
                                self.Handle_EpsonFiscalDriver.getReturnCode())

                    # Adding Receipt Ref Order NUmber in Comment Line
                    self.create_command(
                        CMNT_LINE, "", "Recipet ref: "+str(orders.get('name')))
                    self.Handle_EpsonFiscalDriver.SendCommand()
                    if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                        raise Exception(
                            self.Handle_EpsonFiscalDriver.getReturnCode())

                    # 8 Add Comment Line
                    if self.pos_config.get('receipt_footer'):
                        comment_lines = self.pos_config.get(
                            'receipt_footer').split('\n')
                        for line in comment_lines:
                            if len(line):
                                self.create_command(CMNT_LINE, "", str(line))
                                self.Handle_EpsonFiscalDriver.SendCommand()
                                if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                                    raise Exception(
                                        self.Handle_EpsonFiscalDriver.getReturnCode())

                # 9 Close port
                self.create_command(TXN_CLOSE, "\x00\x00",
                                    "1", "", "", "", "", "")
                self.Handle_EpsonFiscalDriver.SendCommand()
                if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                    raise Exception(
                        self.Handle_EpsonFiscalDriver.getReturnCode())

        except Exception as e:
            _logger.error('Fiscal Printing Comand Error: ', e.args)
            self.create_command(TXN_CANCEL, "\x00\x00")
            self.Handle_EpsonFiscalDriver.SendCommand()
            return e.args
        finally:
            self.Handle_EpsonFiscalDriver.ClosePort()

    @api.model
    def _format_value(self, str1, str2, main):

        new_val = format(main, '.'+str(str2)+'f')
        final = str(new_val).zfill(str1+str2+1)
        final_str = final.replace(".", "")
        return final_str

    def init_fiscal_driver(self, port):
        try:
            _logger.info('Initialize Fiscal Printer Driver')
            path = get_module_resource(
                'hw_blackbox_curacao', 'escpos', 'lib', 'libEpsonFiscalDriver.so')
            self.Handle_EpsonFiscalDriver = ctypes.cdll.LoadLibrary(path)
            Protocol = 1
            self.Handle_EpsonFiscalDriver.setProtocolType(Protocol)
            self.Handle_EpsonFiscalDriver.setComPort(port)
            self.Handle_EpsonFiscalDriver.setBaudRate(9600)
        except:
            _logger.error(
                'Odoo module hw_blackbox_curacao depends on the libEpsonFiscalDriver.so module')

    def create_command(self, cmd, ext, *args):
        if isinstance(cmd, str):
            cmd = bytes(cmd, 'utf-8')
        if isinstance(ext, str):
            ext = bytes(ext, 'utf-8')
        self.Handle_EpsonFiscalDriver.AddDataField(cmd, 2)
        self.Handle_EpsonFiscalDriver.AddDataField(ext, 2)
        for field in args:
            length = len(str(field))
            if isinstance(field, str):
                field = bytes(field, 'utf-8')
            self.Handle_EpsonFiscalDriver.AddDataField(field, length)

    def send_command(self):
        try:
            self.Handle_EpsonFiscalDriver.SendCommand()
            if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                raise Exception(self.Handle_EpsonFiscalDriver.getReturnCode())
            return 0
        except Exception as e:
            _logger.error('Fiscal Printing Error:', e.args)
            return e.args
        finally:
            self.Handle_EpsonFiscalDriver.ClosePort()

    def make_nkf(self, vat, cr_number, reciept_type, txn_number):
        txn_number = re.sub("\D", "", txn_number)
        nkf = "O"+str(vat)+"{0}".format(str(cr_number).zfill(2)
                                        )+str(reciept_type)+txn_number
        return nkf

    @http.route(['/action_z_closure'], type='json', auth="none", cors='*')
    def action_z_closure(self, **kwargs):
        self.init_fiscal_driver(kwargs.get('com_port'))
        self.Handle_EpsonFiscalDriver.OpenPort()
        if (self.Handle_EpsonFiscalDriver.getLastError()):
            return self.Handle_EpsonFiscalDriver.getLastError()
        self.create_command(Z_CLOSUER, '\x00\x01')
        return self.send_command()

    @http.route(['/action_extended_z_report'], type='json', auth="none", cors='*')
    def action_extended_z_report(self, **kwargs):
        self.init_fiscal_driver(kwargs.get('com_port'))
        self.Handle_EpsonFiscalDriver.OpenPort()
        if (self.Handle_EpsonFiscalDriver.getLastError()):
            self.Handle_EpsonFiscalDriver.ClosePort()
            return self.Handle_EpsonFiscalDriver.getLastError()

        start_date = datetime.datetime.strptime(
            str(kwargs.get('start_date')), '%Y-%m-%d %H:%M:%S').strftime('%d%m%Y')
        end_date = datetime.datetime.strptime(
            str(kwargs.get('end_date')), '%Y-%m-%d %H:%M:%S').strftime('%d%m%Y')

        start_z_no = kwargs.get('start_z_no')
        end_z_no = kwargs.get('end_z_no')
        report_type = kwargs.get('report_type')

        if report_type == '1':
            self.create_command(
                Z_CLOSUER_DT_RNG, '\x00\x01', start_date, end_date)
            self.Handle_EpsonFiscalDriver.SendCommand()
            if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                rtn_code = self.Handle_EpsonFiscalDriver.getReturnCode()
                self.create_command(Z_CLOSUER_CANCEL, '')
                self.Handle_EpsonFiscalDriver.SendCommand()
                self.Handle_EpsonFiscalDriver.ClosePort()
                return rtn_code
            rtn_code = 2057

            while rtn_code == 2057:
                rtn_code = 0
                self.create_command(Z_CLOSUER_GET_DATA, '')
                self.Handle_EpsonFiscalDriver.SendCommand()
                if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                    rtn_code = self.Handle_EpsonFiscalDriver.getReturnCode()
                    self.create_command(Z_CLOSUER_CANCEL, '')
                    self.Handle_EpsonFiscalDriver.SendCommand()
                    self.Handle_EpsonFiscalDriver.ClosePort()
                    return rtn_code

                self.create_command(Z_CLOSUER_FINISH, '')
                self.Handle_EpsonFiscalDriver.SendCommand()
                if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                    rtn_code = self.Handle_EpsonFiscalDriver.getReturnCode()
            self.Handle_EpsonFiscalDriver.ClosePort()
            return 0
        elif report_type == '2':
            self.create_command(Z_CLOSUER_Z_RNG, '\x00\x01',
                                str(start_z_no), str(end_z_no))
            self.Handle_EpsonFiscalDriver.SendCommand()
            if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                rtn_code = self.Handle_EpsonFiscalDriver.getReturnCode()
                self.create_command(Z_CLOSUER_CANCEL, '')
                self.Handle_EpsonFiscalDriver.SendCommand()
                self.Handle_EpsonFiscalDriver.ClosePort()
                return rtn_code
            rtn_code = 2057

            while rtn_code == 2057:
                rtn_code = 0
                self.create_command(Z_CLOSUER_GET_DATA, '')
                self.Handle_EpsonFiscalDriver.SendCommand()
                if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                    rtn_code = self.Handle_EpsonFiscalDriver.getReturnCode()
                    self.create_command(Z_CLOSUER_CANCEL, '')
                    self.Handle_EpsonFiscalDriver.SendCommand()
                    self.Handle_EpsonFiscalDriver.ClosePort()
                    return rtn_code

                self.create_command(Z_CLOSUER_FINISH, '')
                self.Handle_EpsonFiscalDriver.SendCommand()
                if (self.Handle_EpsonFiscalDriver.getReturnCode()):
                    rtn_code = self.Handle_EpsonFiscalDriver.getReturnCode()
            self.Handle_EpsonFiscalDriver.ClosePort()
            return 0
        elif report_type == '3':
            self.create_command(INFO_DT_RNG, '\x00\x01', start_date, end_date)
            return self.send_command()
        else:
            self.create_command(INFO_Z_RNG, '\x00\x01',
                                str(start_z_no), str(end_z_no))
            return self.send_command()

    @http.route(['/action_x_report'], type='json', auth="none", cors='*')
    def action_x_report(self, **kwargs):
        self.init_fiscal_driver(kwargs.get('com_port'))
        self.Handle_EpsonFiscalDriver.OpenPort()
        if (self.Handle_EpsonFiscalDriver.getLastError()):
            return self.Handle_EpsonFiscalDriver.getLastError()
        self.create_command('\x08\x05', '')
        return self.send_command()

    @http.route(['/action_set_date_time'], type='json', auth="none", cors='*')
    def action_set_date_time(self, **kwargs):
        self.init_fiscal_driver(kwargs.get('com_port'))
        data = kwargs.get('date_time').split('_')
        self.Handle_EpsonFiscalDriver.OpenPort()
        if (self.Handle_EpsonFiscalDriver.getLastError()):
            return self.Handle_EpsonFiscalDriver.getLastError()
        self.create_command(SET_DATE_TIME, "", str(data[0]), str(data[1]))
        return self.send_command()

    @http.route(['/action_set_permission'], type='json', auth="none", cors='*')
    def set_com_port_permission(self, **kwargs):
        sudoPassword = kwargs.get('password')
        command = "echo %s|sudo -S chmod 777 /dev/ttyUSB0" % sudoPassword
        ps = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        output = ps.communicate()[0]
        _logger.warning(output or "Permission modified")
        res = {}
        if output.find(b'No such file') != -1:
            res['error'] = 'Device not found'
        elif output.find(b'incorrect password') != -1:
            res['error'] = 'incorrect password'
        else:
            res['error'] = False
        return res
