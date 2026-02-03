# -*- coding: utf-8 -*-
# from odoo import http


# class RtBankFeesAccount(http.Controller):
#     @http.route('/rt_bank_fees_account/rt_bank_fees_account/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rt_bank_fees_account/rt_bank_fees_account/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('rt_bank_fees_account.listing', {
#             'root': '/rt_bank_fees_account/rt_bank_fees_account',
#             'objects': http.request.env['rt_bank_fees_account.rt_bank_fees_account'].search([]),
#         })

#     @http.route('/rt_bank_fees_account/rt_bank_fees_account/objects/<model("rt_bank_fees_account.rt_bank_fees_account"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rt_bank_fees_account.object', {
#             'object': obj
#         })
