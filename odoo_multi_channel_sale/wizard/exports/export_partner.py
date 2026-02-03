# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ExportPartner(models.TransientModel):
    _name = 'export.partners'
    _description = 'Export Partner'
    _inherit = 'export.operation'

    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Partner'
    )
