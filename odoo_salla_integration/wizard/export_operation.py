# -*- coding: utf-8 -*-

from odoo import models

# Export category
class ExportCategory(models.TransientModel):
    _inherit = "export.categories"

    def export_salla_categories(self):
        return self.env['export.operation'].create(
            {
                'channel_id': self.channel_id.id,
                'operation': self.operation,
            }
        ).export_button()

# Export template
class ExportCategory(models.TransientModel):
    _inherit = "export.templates"

    def export_salla_templates(self):
        return self.env['export.operation'].create(
            {
                'channel_id': self.channel_id.id,
                'operation': self.operation,
            }
        ).export_button()