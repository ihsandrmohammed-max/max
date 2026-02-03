# -*- coding: utf-8 -*-

from odoo import models
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.ERROR)


class PricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    def write(self, vals):
        for rec in self:
            rec.product_tmpl_id.channel_mapping_ids.write({'need_sync': 'yes'})
            rec.product_id.channel_mapping_ids.write({'need_sync': 'yes'})
            rec.product_id.product_tmpl_id.channel_mapping_ids.write({'need_sync': 'yes'})
        return super().write(vals)
