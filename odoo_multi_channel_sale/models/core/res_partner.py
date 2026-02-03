# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    channel_mapping_ids = fields.One2many(
        string='Mappings',
        comodel_name='channel.partner.mappings',
        inverse_name='odoo_partner',
        copy=False
    )
