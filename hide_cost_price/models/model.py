# # -*- coding: utf-8 -*-
# from odoo import api, fields, models
#
#
# class ProductTemplate(models.Model):
#     _inherit = 'product.template'
#
#     # standard_price = fields.Float(
#     #     exportable=False,)
#
#     standard_price = fields.Float(
#         'Cost', compute='_compute_standard_price',
#         inverse='_set_standard_price', search='_search_standard_price',
#         digits='Product Price',
#         help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
#         In FIFO: value of the next unit that will leave the stock (automatically computed).
#         Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
#         Used to compute margins on sale orders.""")
#
#     @api.model
#     def fields_get(self,allfields=None, attributes=None):
#         res = super(ProductTemplate, self).fields_get(allfields=allfields, attributes=attributes)
#         print('=================RES================',res)
#         # readable_fields = self.SELF_READABLE_FIELDS
#         # public_fields = {field_name:standard_price  for field_name, standard_price in fields.items() if
#         #                  field_name in readable_fields}
#         fields_to_hide = res['standard_price']
#
#         fields = self.fields_get()
#
#         print('===============Hide',fields,'============',fields_to_hide)
#         # for field in fields_to_hide:
#         if 'standard_price' in res['standard_price'] and not self.env.user.has_group('hide_cost_price.view_cost_price'):
#             # print('====================RES FEild',res[field])
#             # res[field]['searchable'] = False
#             res['standard_price']['exportable'] = False
#         return res
#     # @api.model
#     # def fields_get(self, allfields=None, attributes=None):
#     #     fields_to_hide = ['standard_price']
#     #     fields_to_hide = {field_name: cost for field_name, cost in fields.items() if field_name in readable_fields}
#     #
#     #     res = super(ProductTemplate, self).fields_get(allfields=allfields, attributes=attributes)
#     #     # print('===========Res==========',res[standard_price])
#     #     # labels = dict(self.fields_get(['standard_price'])['state']['selection'])
#     #     fields_to_hide = ['standard_price']
#     #     for field in fields_to_hide:
#     #         if not self.env.user.has_group('hide_cost_price.view_cost_price'):
#     #             # res[field]['searchable'] = False
#     #             res[field]['exportable'] = False
#     #     return res
#     # @api.model
#     # def fields_get(self):
#     #     fields_to_hide = ['standard_price']
#     #     res = super(ProductTemplate, self).fields_get(allfields=allfields, attributes=attributes)
#     #     for field in fields_to_hide:
#     #         if not self.env.user.has_group('hide_cost_price.view_cost_price'):
#     #             res[field]['searchable'] = False
#     #             res[field]['exportable'] = False
#     #     return res
#
#
# class ProductProduct(models.Model):
#     _inherit = 'product.product'
#
#     standard_price = fields.Float(
#         'Cost', company_dependent=True,
#         digits='Product Price',
#         help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
#               In FIFO: value of the next unit that will leave the stock (automatically computed).
#               Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
#               Used to compute margins on sale orders.""")
#
#     # @api.model
#     # def fields_get(self, allfields=None, attributes=None):
#     #     fields_to_hide = ['standard_price']
#     #
#     #     res = super(ProductProduct, self).fields_get(allfields, attributes)
#     #     for field in fields_to_hide:
#     #         if not self.env.user.has_group('hide_cost_price.view_cost_price'):
#     #             res[field]['searchable'] = False
#     #             res[field]['exportable'] = False
#     #     return res
#
#
# class StockQuant(models.Model):
#     _inherit = 'stock.quant'
#
#     # @api.model
#     # def fields_get(self, fields=None):
#     #     fields_to_hide = ['value']
#     #     res = super(StockQuant, self).fields_get()
#     #     for field in fields_to_hide:
#     #         if not self.env.user.has_group('hide_cost_price.view_cost_price'):
#     #             res[field]['searchable'] = False
#     #             res[field]['exportable'] = False
#     #     return res
#
#
# class StockValuationLayer(models.Model):
#     _inherit = 'stock.valuation.layer'
#
#     # @api.model
#     # def fields_get(self, fields=None):
#     #     fields_to_hide = ['value']
#     #     res = super(StockValuationLayer, self).fields_get(attributes=['invisible', 'states', 'readonly', 'required'])
#     #     for field in fields_to_hide:
#     #         if not self.env.user.has_group('hide_cost_price.view_cost_price'):
#     #             res[field]['searchable'] = False
#     #             res[field]['exportable'] = False
#     #     return res
