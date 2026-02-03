# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ImportAttribute(models.TransientModel):
    _name = 'import.attributes'
    _description = 'Import Attribute'
    _inherit = 'import.operation'

    attribute_ids = fields.Text('Attribute ID(s)')
