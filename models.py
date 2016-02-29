from openerp import models, fields, api
from openerp.tools.float_utils import float_round
class extend_mro(models.Model):
    _inherit = "mro.order"

    labor_fields_id = fields.One2many('tree_labor','tree_labor_id')
    workshop_name = fields.Char("Name of Workshop")
    actual_time_taken = fields.Datetime('Actual Time Taken')
    workshop_ids = fields.One2many('work_shop','work_shop_id')
    def _compute_stock_move(self):
        self.stock_move_ids = self.mapped('parts_lines.stock_move_id')
    stock_move_ids = fields.Many2many(
        comodel_name='stock.move', compute='_compute_stock_move',
        string='Stock Moves')
    @api.multi
    def write(self, values):
        result = super(extend_mro, self).write(values)
        for rec in self:
            rec.parts_lines.create_stock_move()
        return result

    @api.multi
    def action_assign(self):
        self.mapped('stock_move_ids').action_assign()

    @api.multi
    def action_done(self):
        self.mapped('stock_move_ids').action_done()


class stock_move_mro(models.Model):
    _inherit = "mro.order.parts.line"
    stock_move_id = fields.Many2one(
        comodel_name='stock.move', string='Stock Move')
    product_unit_price = fields.Float("Unit Price")
    total_price = fields.Float("Total")


    def _prepare_stock_move(self):
        product = self.parts_id
        res = {
            'product_id': product.id,
            'name': product.name,
            'product_uom': self.parts_uom.id,
            'product_uom_qty': self.parts_qty,
            'location_id': self.env.ref(
            'stock.stock_location_stock').id,
            'location_dest_id': self.env.ref(
            'stock.stock_location_customers').id,
        }
        return res

    @api.multi
    def create_stock_move(self):
        for line in self:
            move_id = self.env['stock.move'].create(
                line._prepare_stock_move())
            line.stock_move_id = move_id.id

#mro request inherit clall
class extend_mro_request(models.Model):
    _inherit = "mro.request"
    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle No & Model")
    responded_time = fields.Datetime("Responded Time")
    action_taken_description = fields.Text("Action Taken")

class inherit_fleet_module(models.Model):
    _inherit = 'fleet.vehicle'
    
#tree_labor class tree_labor
class tree_labor(models.Model):
    _name = 'tree_labor'
    mechanics = fields.Char("Mechanics")
    description_wrk_done = fields.Char("Description of Work Done")
    start_time = fields.Datetime("Start")
    stop_time = fields.Datetime("End")
    total_time = fields.Datetime("Total Time")
    tree_labor_id = fields.Many2one('mro.order')

#work_shop class work shop
class work_shop(models.Model):
    _name = 'work_shop'
    wrk_shop_des = fields.Char("Mechanics")
    parts_materials = fields.Char("Description of Work Done")
    wrk_shop_qty = fields.Float("Quantity")
    wrk_shop_price = fields.Float("Unit Price")
    wrk_shop_total = fields.Float("Total")
    work_shop_id = fields.Many2one('mro.order')