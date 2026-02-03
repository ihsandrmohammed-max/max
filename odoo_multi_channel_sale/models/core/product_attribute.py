# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    # @api.model
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self._context.get('odoo_multi_attribute') or self._context.get('install_mode'):
                obj = self.search([('name', '=ilike', vals.get('name').strip(' '))], limit=1)
                if obj:
                    return obj
        return super(ProductAttribute, self).create(vals_list)
