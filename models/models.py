from datetime import timedelta
from odoo import fields, models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_history_ids = fields.One2many(
        comodel_name='order.history',
        inverse_name='order_id',
        string='Order History'
    )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self._clear_order_history()
            config_params = self._get_config_params()
            domain = self._build_order_domain(config_params)
            sale_orders = self._fetch_sale_orders(
                domain, 
                config_params['last_no_of_orders']
                )
            histories = self._prepare_order_histories(
                sale_orders, 
                config_params['last_no_of_orders']
                )
            self.order_history_ids = histories

    def _clear_order_history(self):
        self.order_history_ids = [(5, 0, 0)]

    def _get_config_params(self):
        config_param = self.env['ir.config_parameter'].sudo()
        return {
            'last_no_of_orders': int(config_param.get_param(
                'sale.last_no_of_orders', 0)),
            'last_no_of_days': int(config_param.get_param(
                'sale.last_no_of_days', 0)),
            'order_stages': config_param.get_param(
                'sale.order_stages', 
                'all'),
        }

    def _build_order_domain(self, config_params):
        domain = [(
            'partner_id', '=', self.partner_id.id)
            ]
        if config_params['order_stages'] != 'all':
            domain.append(
                ('state', '=', config_params['order_stages'])
                )
        else:
            domain.append(
                ('state', 
                 'in', 
                 ['draft', 'sent', 'sale', 'done', 'cancel'])
                 )
        if config_params['last_no_of_days']:
            today = fields.Date.today()
            start_date = fields.Date.to_string(today - timedelta(days=config_params[
                'last_no_of_days'])
                )
            domain.append((
                'date_order', '>=', start_date)
                )
        return domain

    def _fetch_sale_orders(self, domain, limit):
        return self.env['sale.order'].search(
            domain, 
            order='date_order desc', 
            limit=limit)

    def _prepare_order_histories(self, sale_orders, limit):
        histories = []
        for order in sale_orders:
            for line in order.order_line:
                if len(histories) < limit:
                    histories.append((0, 0, {
                        'order_id': order.id,
                        'order_line_id': line.id,
                        'name': order.name,
                        'date_order': order.date_order,
                        'product_id': line.product_id.id,
                        'price': line.price_unit,
                        'qty_unit': line.product_uom_qty,
                        'discount': line.discount,
                        'amount_total': line.price_subtotal,
                        'state': order.state,
                    }))
                else:
                    break
        return histories

    def action_reorder(self):
        if not self.env['ir.config_parameter'].sudo().get_param(
            'sale.enable_reorder', 
            False):
            return {
                'type': 'ir.actions.act_window',
                'name': 'Reorder Disabled',
                'view_mode': 'form',
                'res_model': 'res.config.settings',
                'target': 'new',
                'context': {'default_enable_reorder': False},
            }

        new_order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
        })

        order_lines = []
        for history in self.order_history_ids.filtered('order_history_selected'):
            order_lines.append((0, 0, {
                'product_id': history.product_id.id,
                'product_uom_qty': history.qty_unit,
                'price_unit': history.price,
                'discount': history.discount,
            }))
        new_order.write({'order_line': order_lines})

        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': new_order.id,
            'target': 'current',
        }

class OrderHistory(models.Model):
    _name = 'order.history'
    _description = 'Order History'

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string="Order"
    )
    order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Order Line'
    )
    order_history_selected = fields.Boolean(
        string='Re-Order'
    )
    name = fields.Char(
        string='Sale Order'
    )
    date_order = fields.Datetime(
        string='Order Date'
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product'
    )
    price = fields.Float(
        string='Price'
    )
    qty_unit = fields.Float(
        string='Quantity Unit'
    )
    discount = fields.Float(
        string='Discount'
    )
    amount_total = fields.Float(
        string='Sub Total',
        compute='_compute_amount_total',
        store=True
    )
    state = fields.Selection(
        string='Order Status',
        selection=[
            ('draft', 'Quotation'),
            ('sent', 'Quotation Sent'),
            ('sale', 'Sale Order'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ],
    )

    @api.depends('price', 'qty_unit', 'discount')
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = (record.price * record.qty_unit) - record.discount

    def action_reorder(self):
        if self.order_id:
            self.write({'order_history_selected': True})
            return self.order_id.action_reorder()

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    last_no_of_orders = fields.Integer(
        "Last Number of Orders",
        config_parameter='sale.last_no_of_orders'
    )
    order_stages = fields.Selection(
        [('all', 'All'),
         ('draft', 'Quotation'),
         ('sent', 'Quotation Sent'),
         ('sale', 'Sale Order'),
         ('done', 'Done'),
         ('cancel', 'Cancelled')],
        config_parameter='sale.order_stages',
        string="Order Stages",
        help="Stages of the orders",
        default='all'
    )
    last_no_of_days = fields.Integer(
        "Last Number of Days for Orders",
        config_parameter='sale.last_no_of_days'
    )
    enable_reorder = fields.Boolean(
        "Enable Reorder",
        config_parameter='sale.enable_reorder'
    )
