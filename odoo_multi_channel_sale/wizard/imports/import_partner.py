# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ImportPartner(models.TransientModel):
    _name = 'import.partners'
    _description = 'Import Partner'
    _inherit = 'import.operation'

    partner_ids = fields.Text('Partners ID(s)')
