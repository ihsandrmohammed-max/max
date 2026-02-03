{
    'name': 'Omniful Integration',
    'version': '18.0.1.0.1',
    'category': 'Integration',
    'summary': 'Integration with Omniful system',
    'description': """
        This module provides integration with Omniful system.
        Features:
        - Temporary inventory management
        - API configuration settings
        - Data synchronization
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'sale_management', 'odoo_salla_integration'],
    'data': [
        'security/ir.model.access.csv',

        'views/temp_inventory_views.xml',
        'views/inventory_feed_views.xml',
        'views/channel_omniful_views.xml',
        'views/order_feed_views.xml',
        'views/product_feed_views.xml',
        'views/purchase_feed_views.xml',
        'views/shipment_feed_views.xml',
        'views/shipment_feed_views.xml',
        'views/stock_feed_views.xml',
        'views/product_custom.xml',
        'views/res_partner.xml',
        'views/sale_order_view.xml',

        'views/menu.xml',

        'data/ir_config_parameter_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}