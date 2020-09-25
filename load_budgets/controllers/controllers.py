# -*- coding: utf-8 -*-
from odoo import http

# class LoadBudgets(http.Controller):
#     @http.route('/load_budgets/load_budgets/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/load_budgets/load_budgets/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('load_budgets.listing', {
#             'root': '/load_budgets/load_budgets',
#             'objects': http.request.env['load_budgets.load_budgets'].search([]),
#         })

#     @http.route('/load_budgets/load_budgets/objects/<model("load_budgets.load_budgets"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('load_budgets.object', {
#             'object': obj
#         })