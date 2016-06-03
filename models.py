from openerp import models, fields, api
from openerp.tools.float_utils import float_round
from datetime import date, datetime
class extend_mro(models.Model):
    _inherit = "mro.order"

    labor_fields_id = fields.One2many('tree_labor','tree_labor_id')
    workshop_name = fields.Char("Name of Workshop")
    actual_time_taken = fields.Datetime('Actual Time Taken')
    workshop_ids = fields.One2many('work_shop','work_shop_id')
    m_source_location = fields.Many2one('stock.location','Source Location', required=True)
    m_destination_location = fields.Many2one('stock.location','Destination Location', required=True)
    odoo_meter_value = fields.Float('Odoometer Value')
    total_part_price = fields.Float(string='Total Parts',store=True, readonly=True, compute='_compute_tpamount')
    total_market_price = fields.Float(string='Total Market',store=True, readonly=True, compute='_compute_twamount')
    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle No & Model")
    material_transfered = fields.Char("Material Status", readonly=True)
    def _compute_stock_move(self):
        self.stock_move_ids = self.mapped('parts_lines.stock_move_id')
    stock_move_ids = fields.Many2many(
        comodel_name='stock.move', compute='_compute_stock_move',
        string='Stock Moves')
    @api.model
    def create(self, values):
        result = super(extend_mro, self).create(values)
        if values['fleet_vehicle_id']:
            vehicle_cost = self.env['fleet.vehicle.cost']
            price = 0
            vehicle_cost_type = self.env['fleet.service.type'].search([('name','=','Repair and maintenance')])
            for value in values['parts_lines']:
                price = price + value[2]['total_price']
                print price
            res = {
            'vehicle_id' : values['fleet_vehicle_id'],
            'cost_subtype_id' : vehicle_cost_type.id,
            'amount' : price,
            'date' : values['date_planned'],
            }
            vehicle_cost.create(res)
        return result

#    @api.multi
#    def action_assign(self):
#        self.mapped('stock_move_ids').action_assign()

#    @api.multi
#    def action_done(self):
#        self.mapped('stock_move_ids').action_done()


    @api.one
    @api.depends('parts_lines.total_price')
    def _compute_tpamount(self):
        self.total_part_price = sum(line.total_price for line in self.parts_lines) 

    @api.one
    @api.depends('workshop_ids.wrk_shop_total')
    def _compute_twamount(self):
        self.total_market_price = sum(line.wrk_shop_total for line in self.workshop_ids)
    @api.multi
    def _prepare_mo_workbook_one_ids(self):
        new_data = []
        all_recd_consume = self.parts_lines
        for line in all_recd_consume:
            data = self._prepare_workbook_one_line(line)
            new_data.append(data)
        return new_data
    @api.multi
    def _prepare_workbook_one_line(self, data):
        data = {
            'product_id': data.parts_id,
            'name': data.parts_id.name,
            'product_uom': data.parts_uom.id,
            'product_uom_qty': data.parts_qty,
            'location_id' : self.m_source_location.id,
            'location_dest_id' : self.m_destination_location.id,
            #'location_id': self.env.ref(
            #'stock.stock_location_stock').id,
            #'location_dest_id': self.env.ref(
            #'stock.stock_location_customers').id,
            }
        return data
    @api.multi
    def update_consume_history(self, values):
        whare_house_type = self.env['stock.picking.type'].search([('name','=','Delivery Orders')])
        whare_house = self.env['stock.picking']
        whare_house_move_lines = self._prepare_mo_workbook_one_ids()
        values = {
        'move_type': 'direct',
        'invoice_state': 'none',
        'picking_type_id': whare_house_type.id,
        'company_id': self.company_id.id,
        'priority': '1',
        'maintaince_order_ref_id' : self.id,
        }
        whare_house.create(values)
        records = self.env['stock.picking'].search([('maintaince_order_ref_id','=',self.id)])
        records.move_lines= self._prepare_mo_workbook_one_ids()
        self.material_transfered = "YES"
        records.write({'state':'done'})


class stock_move_mro(models.Model):
    _inherit = "mro.order.parts.line"
    stock_move_id = fields.Many2one(
        comodel_name='stock.move', string='Stock Move')
    product_unit_price = fields.Float("Unit Price")
    total_price = fields.Float("Total")


#    def _prepare_stock_move(self):
#        product = self.parts_id
#        maintaince_order_recs = self.env['mro.order'].search([('id','=',self.maintenance_id.id)])
#        res = {
#            'product_id': product.id,
#            'name': product.name,
#            'product_uom': self.parts_uom.id,
#            'product_uom_qty': self.parts_qty,
#            'location_id': self.env.ref(
#            'stock.stock_location_stock').id,
#            'location_dest_id': self.env.ref(
#            'stock.stock_location_customers').id,
#            'maintaince_order_ref' : maintaince_order_recs.id,
#            'location_id' : maintaince_order_recs.m_source_location.id,
#            'location_dest_id' : maintaince_order_recs.m_destination_location.id,
#        }
#        return res

#    @api.multi
#    def create_stock_move(self):
#        for line in self:
#            move_id = self.env['stock.move'].create(
#                line._prepare_stock_move())
#            line.stock_move_id = move_id.id

    @api.one
    @api.depends('parts_id')
    def _compute_unit_price(self):
        self.product_unit_price = self.parts_id.standard_price 

    @api.one
    @api.depends('parts_id','parts_qty')
    def _compute_total_price(self):
        self.total_price = self.parts_id.standard_price * self.parts_qty      

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


#stock move class
class mro_alfateh_stock_move(models.Model):
    _inherit = 'stock.move'
    maintaince_order_ref = fields.Many2one('mro.order',string="MRO Order Ref") 


class mro_alfateh_stock_picking(models.Model):
    _inherit = 'stock.picking'
    maintaince_order_ref_id = fields.Many2one('mro.order',string="MRO Order Ref") 