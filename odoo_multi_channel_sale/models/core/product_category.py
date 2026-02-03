# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    channel_mapping_ids = fields.One2many(
        string='Mappings',
        comodel_name='channel.category.mappings',
        inverse_name='category_name',
        copy=False
    )

    channel_category_ids = fields.One2many(
        string='Channel Categories',
        comodel_name='extra.categories',
        inverse_name='category_id',
        copy=False
    )

    def write(self, vals):
        self.mapped('channel_mapping_ids').write({'need_sync': 'yes'})
        res = super(ProductCategory, self).write(vals)
        return res

    def unlink(self):
        for obj in self:
            self.env['multi.channel.sale'].unlink_feeds_mapping(obj.channel_mapping_ids, obj)
        return super(ProductCategory, self).unlink()
