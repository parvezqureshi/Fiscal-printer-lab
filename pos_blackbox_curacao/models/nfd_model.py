from odoo import models, api, fields
from collections import defaultdict


class NFD_Model(models.Model):
    _inherit = 'pos.order'

    @api.model
    def get_json_receipt(self, pos_config_id, order_id):
        total_item_wise_discount = 0
        line = self.env['pos.order.line']
        tax = account_tax = self.env['account.tax']
        bank_statement_line = self.env['account.bank.statement.line']
        pos_order = self.env['pos.order'].browse(order_id)
        pos_config = self.env['pos.config'].browse(pos_config_id)
        company = self.env['res.partner'].browse(pos_order.company_id.id)
        params = {
            'company': {},
            'orderlines': [],
            'tax_details': [],
            'paymentlines': [],
            'precision': {},
            'proxy_ip': pos_config.proxy_ip,
            'com_port': pos_config.com_port,
            'header': pos_config.receipt_header,
            'footer': pos_config.receipt_footer,
            'cashier': pos_order.create_uid.id,
            'subtotal': pos_order.amount_total,
            'total_with_tax': pos_order.amount_total,
            'name': pos_order.pos_reference,
            'date_order': fields.Date.to_string(pos_order.date_order),
            'change': -1*pos_order.amount_return,
        }
        params['precision'] = {
            'money': 2,
            'price': 2,
            'quantity': 3,
        }
        params['company'] = {
            'name': pos_order.company_id.name,
            'contact_address': company.street,
            'phone': company.phone,
            'vat': company.crib,
            'email': company.email,
            'website': company.website,
        }

        for idx, order_line in enumerate(pos_order.lines):
            pos_order_line = line.browse(order_line.id)
            params['orderlines'].append({
                'unit_name': 'Qty',
                'quantity': pos_order_line.qty or 0,
                'discount': pos_order_line.discount or 0,
                'price_display': pos_order_line.price_unit or 0,
                'product_name': pos_order_line.display_name or '',
                'price': pos_order_line.price_subtotal_incl or 0,
            })
            if pos_order_line.discount > 0:
                total_item_wise_discount += pos_order_line.discount * pos_order_line.price_subtotal_incl / 100
            if pos_order_line.tax_ids_after_fiscal_position.id:
                tax = account_tax.browse(pos_order_line.tax_ids_after_fiscal_position.id)
            params['tax_details'].append({
                'name': tax.name or '',
                'amount': round(pos_order_line.price_subtotal_incl - pos_order_line.price_subtotal, 2) or 0
            })
            params['total_discount'] = total_item_wise_discount

        for payment in pos_order.payment_ids:
            if payment.amount > 0:
                params['paymentlines'].append({
                    'amount': payment.amount,
                    'journal': payment.payment_method_id.name or '',
                })

        return params
