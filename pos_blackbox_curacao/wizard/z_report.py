# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PosZReport(models.TransientModel):
    _name = 'pos.zreport.wizard'
    _description = 'Z Report'

    def _default_start_date(self):
        """ Find the earliest start_date of the latests sessions """
        # restrict to configs available to the user
        config_ids = self.env['pos.config'].search([]).ids
        # exclude configs has not been opened for 2 days
        self.env.cr.execute("""
            SELECT
            max(start_at) as start,
            config_id
            FROM pos_session
            WHERE config_id = ANY(%s)
            AND start_at > (NOW() - INTERVAL '2 DAYS')
            GROUP BY config_id
        """, (config_ids,))
        latest_start_dates = [res['start'] for res in self.env.cr.dictfetchall()]
        # earliest of the latest sessions
        return latest_start_dates and min(latest_start_dates) or fields.Datetime.now()

    start_date = fields.Datetime(required=True, default=_default_start_date)
    end_date = fields.Datetime(required=True, default=fields.Datetime.now)
    start_z_no = fields.Integer(required=True, string="Start Z Number")
    end_z_no = fields.Integer(required=True, string="End Z Number")
    pos_config_id = fields.Many2one('pos.config', string="POS Counter", required=True)

    # Report Type:
    # 1. Z-Report with Date Range
    # 2. Z-Report with Z Number
    # 3. Data Query Z-Report with Date Range
    # 4. Data Query Z-Report with Z Number
    report_type = fields.Selection([('1','Z closures reports by date range'),('2','Z closure report by range of Z closures'),('3','Information by date range'),('4','Information by Z closures range')], string="Report Type", help="Type Of Z-Report to be Print", required=True, default='1')

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            self.end_date = self.start_date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date and self.end_date < self.start_date:
            self.start_date = self.end_date

    def generate_zreport(self):
        # Just to Avoid Undefined Error
        # Main Stuff is happening at data_model.js
        pass
