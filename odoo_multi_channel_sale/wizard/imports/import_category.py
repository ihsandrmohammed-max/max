# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ImportCategory(models.TransientModel):
    _name = 'import.categories'
    _description = 'Import Category'
    _inherit = 'import.operation'

    category_ids = fields.Text('Categories ID(s)')
    parent_categ_id = fields.Many2one('channel.category.mappings', 'Parent Category')
