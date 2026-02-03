# -*- coding: utf-8 -*-

{
    'name':  'Salla Odoo Connector | Odoo Multichannel',
    'summary':              """
                            Odoo Salla Connectors integrates your Odoo with salla to make 
                            the shopping experience seamless. The module allows you to 
                            sync products, categories, and sync orders to Odoo so that 
                            you can efficiently manage.
                            Multichannel is also compatible with these Rightechs-solutions apps
                            Amazon Connector Ebay Connector Magento Connector Woocommerce
                            Connector Shopify Connector Shopware Connector Walmart Wix Connector
                            Connector Prestashop Connector flipkart connector odoo Apps
                            Ecommerce Connectors for salla multi-channel salla Rightechs-solutions connectors
                            """,
    'description':          """
                                Salla Connector for Multichannel
                                Integrate Salla E-Commerce with Odoo.
                                Odoo Salla Connector integrates your Odoo with Salla to make the shopping experience seamless. 
                                The module allows you to sync products, categories, and orders to Odoo so that you can efficiently manage. 
                            """,
    'category': 'eCommerce',
    'version': '1.1.4',
    'sequence': 1,
    'author': 'rightechs-solutions Pvt. Ltd.',
    'maintainer': 'rightechs-solutions Software Pvt. Ltd.',
    'license': 'Other proprietary',
    'website': 'https://rightechs-solutions.odoo.com/',
    'live_test_url': 'https://rightechs-solutions.odoo.com/',
    'depends': ['odoo_multi_channel_sale'],
    'data': [
        'data/data.xml',
        'data/ir_cron.xml',
        'views/multi_channel_sale.xml',
        'wizard/import_operation.xml',
        'wizard/export_operation.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_salla_integration/static/src/xml/instance_dashboard.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'price': 199,
    'currency': 'USD',
    'pre_init_hook': 'pre_init_check',
}
