from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.depends('move_lines')
    def _compute_inspection(self):
        '''
        This function computes the number of quality inspections generated from given picking.
        '''
        for picking in self:
            alerts = self.env['qc.inspection'].search([('picking_ids', 'in', picking.id)])
            picking.inspection_ids = alerts
            picking.inspection_count = len(alerts)
        print(self.inspection_count)

    @api.multi
    def quality_inspection_action(self):
        '''This function returns an action that display existing quality alerts generated from a given picking.'''
        return {
            'name': _('Picking quality inspection'),
            'view_mode': 'tree,form',
            'res_model': 'qc.inspection',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('picking_ids', '=', self.id)],

        }

    inspection_count = fields.Integer(compute='_compute_inspection', string='Quality inspections', default=0)
    inspection_ids = fields.One2many('qc.inspection', 'picking_ids', string='Quality Inspection',
                                     copy=False)

    # -----------------------------------------------------------------------------
    @api.multi
    def generate_quality_inspection(self):
        '''
        This function generates quality inspections for the products mentioned in move_lines of given picking and also have trigger configured.
        '''
        lines = []
        products = []
        quality_inspection = self.env['qc.inspection']
        quality_question = self.env['qc.inspection.line']
        for move in self.move_lines:
            product_id = self.env['product.template'].search(
                [('id', '=', move.product_id.product_tmpl_id.id)])
            questions = quality_question.search(
                [('product_id', '=', product_id.id), ('trigger_time_ids', 'in', self.picking_type_id.ids)])
            if questions:
                for line in questions:
                    lines.append(line.id)
                    if move.product_id.id not in products:
                        products.append(move.product_id.id)


        id = quality_inspection.create({
            'name': self.env['ir.sequence'].next_by_code('qc.inspection') or _('New'),
            'stock_picking_id': self.picking_type_id.id,
            'product_ids': [(6, 0, products)],
            'picking_ids': [(6, 0, self.ids)],
            'company_id': self.company_id.id,
            'inspection_lines': [(6, 0, lines)],

        })
        import logging
        logging.error(id)

    # @api.multi
    # def action_confirm(self):
    #     if self.inspection_count == 0:
    #         self.generate_quality_inspection()
    #     res = super(StockPicking, self).action_confirm()
    #     return res

    @api.multi
    def force_assign(self):
        if self.inspection_count == 0:
            self.generate_quality_inspection()
        res = super(StockPicking, self).force_assign()
        return res

    @api.multi
    def button_validate(self):
        # if self.inspection_count == 0:
        self.generate_quality_inspection()
        res = super(StockPicking, self).button_validate()
        return res
    #
