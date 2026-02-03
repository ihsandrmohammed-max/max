# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SallaOrderStatus(models.Model):
    _name = 'salla.order.status'
    _description = 'Salla Order Status'
    _order = 'sort, name'
    _rec_name = 'display_name'

    salla_status_id = fields.Integer(
        string='Salla Status ID',
        required=True,
        unique=True,
        index=True,
        help='Unique identifier from Salla platform'
    )
    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        help='Status name'
    )
    type = fields.Char(
        string='Type',
        help='Status type (e.g., custom, system)'
    )
    slug = fields.Char(
        string='Slug',
        help='URL-friendly identifier'
    )
    sort = fields.Integer(
        string='Sort Order',
        default=0,
        help='Display order'
    )
    message = fields.Text(
        string='Message',
        translate=True,
        help='Status message template'
    )
    icon = fields.Char(
        string='Icon',
        help='Icon class name'
    )
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether the status is active'
    )

    # Original status information
    original_id = fields.Integer(
        string='Original Status ID',
        help='Original status ID from Salla'
    )
    original_name = fields.Char(
        string='Original Name',
        translate=True,
        help='Original status name'
    )

    # Parent hierarchy
    parent_id = fields.Many2one(
        'salla.order.status',
        string='Parent Status',
        ondelete='set null',
        help='Parent status in hierarchy'
    )
    parent_salla_id = fields.Integer(
        string='Parent Salla ID',
        help='Parent status Salla ID (used for mapping before hierarchy resolution)'
    )

    # Additional fields
    channel_id = fields.Many2one(
        'multi.channel.sale',
        string='Channel',
        help='Associated channel instance'
    )

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help='Formatted display name: slug (name)'
    )

    @api.depends('slug', 'name')
    def _compute_display_name(self):
        """
        Compute display name format: slug (name) or (name) if slug is empty.
        """
        for record in self:
            name = record.name or ''
            slug = record.slug or ''
            
            if slug:
                record.display_name = f"{slug} ({name})"
            else:
                record.display_name = f"({name})" if name else ''

    def name_get(self):
        """
        Customize record name display format.
        Format: slug (name) or just (name) if slug is empty.
        """
        result = []
        for record in self:
            name = record.name or ''
            slug = record.slug or ''
            
            if slug:
                display_name = f"{slug} ({name})"
            else:
                display_name = f"({name})" if name else ''
            
            result.append((record.id, display_name))
        return result

    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        """Prevent recursive parent relationships"""
        for record in self:
            if record.parent_id:
                parent = record.parent_id
                visited = {record.id}
                while parent:
                    if parent.id in visited:
                        raise UserError(_('Error! You cannot create recursive parent relationships.'))
                    visited.add(parent.id)
                    parent = parent.parent_id
