# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ImportTemplate(models.TransientModel):
    _name = 'import.templates'
    _description = 'Import Template'
    _inherit = 'import.operation'

    product_tmpl_ids = fields.Text('Product Template ID(s)')
    source = fields.Selection(
        selection=[
            ('all', 'All'),
            ('product_tmpl_ids', 'Product ID(s)'),
        ],
        required=True,
        default='all'
    )
