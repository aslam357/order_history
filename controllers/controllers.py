# -*- coding: utf-8 -*-
# from odoo import http


# class OrderHistory(http.Controller):
#     @http.route('/order_history/order_history', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/order_history/order_history/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('order_history.listing', {
#             'root': '/order_history/order_history',
#             'objects': http.request.env['order_history.order_history'].search([]),
#         })

#     @http.route('/order_history/order_history/objects/<model("order_history.order_history"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('order_history.object', {
#             'object': obj
#         })

