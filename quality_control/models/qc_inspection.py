from odoo import api, exceptions, fields, models, _



class QcInspection(models.Model):
    _name = 'qc.inspection'
    _description = 'Quality control inspection'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Inspection number', required=True, default=lambda self: _('New'),
                       readonly=True, copy=False, )

    date = fields.Datetime(
        string='Date', required=True, readonly=True, copy=False,
        default=fields.Datetime.now,
        states={'draft': [('readonly', False)]})

    product_ids = fields.Many2many(
        comodel_name="product.template", help="Product associated with the inspection",required=True,
        oldname='product',domain=lambda self: self.onchange_products_ids())

    product_product_ids = fields.Many2many(comodel_name="product.product", string="product")

    qty = fields.Float(string="Quantity", default=1.0)

    inspection_lines = fields.One2many(
        comodel_name='qc.inspection.line', inverse_name='inspection_id',
        string='Inspection lines', readonly=True,
        states={'ready': [('readonly', False)]})
    internal_notes = fields.Text(string='Internal notes')
    external_notes = fields.Text(
        string='External notes',
        states={'success': [('readonly', True)],
                'failed': [('readonly', True)]})
    state = fields.Selection(
        [('draft', 'Test'),
         ('ready', 'Ready'),
         ('waiting', 'Waiting supervisor approval'),
         ('success', 'Quality success'),
         ('failed', 'Quality failed'),
         ('canceled', 'Canceled')],
        string='State', readonly=True, default='draft',
        track_visibility='onchange')
    success = fields.Boolean(
        compute="_compute_success", string='Success', default=False,
        help='This field will be marked if all tests have succeeded.',
        store=True)
    auto_generated = fields.Boolean(
        string='Auto-generated', readonly=True, copy=False,
        help='If an inspection is auto-generated, it can be canceled but not '
             'removed.')
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get(
            'qc.inspection'))
    user = fields.Many2one(
        comodel_name='res.users', string='Responsible',
        track_visibility='always', default=lambda self: self.env.user)

    category = fields.Many2one(
        comodel_name='qc.test.category', string='Category', required=True)

    team_ids = fields.Many2many('qc.team', string='Teams')

    stock_picking_id = fields.Many2one('stock.picking.type', string='Opération', required=True)

    picking_ids = fields.Many2many('stock.picking', string='Source Operation',
                            required=True)
    operation_ids = fields.Many2many('mrp.production', string='Source Operation')

    @api.depends('inspection_lines', 'inspection_lines.success')
    def _compute_success(self):
        for i in self:
            i.success = all([x.success for x in i.inspection_lines])

    #Sources
    @api.onchange('stock_picking_id')
    def onchange_stock_picking_id(self):
        # vider le champs
        pickings=[]
        self.write({'picking_ids': pickings})
        self.write({'product_ids': pickings})
        #définir le domaine
        domain = {'picking_ids': [('picking_type_id', '=', self.stock_picking_id.id)]}
        return {'domain': domain}

    # Products
    @api.onchange('picking_ids')
    def onchange_products_ids(self):
        #vider le champs
        product_remove=[]
        for product in self.product_ids:
            for picking in self.picking_ids:
                for line in picking.move_lines:
                    product_id = self.env['product.template'].search(
                                 [('id', '=', line.product_id.product_tmpl_id.id)]) #product to product template
                    if product.id == product_id.id:
                        product_remove.append(product_id.id)

        self.update({'product_ids': [(6, 0, product_remove)]})
        #définir le domaine
        products = []
        for picking in self.picking_ids:
            for line in picking.move_lines:
                product_id = self.env['product.template'].search(
                    [('id', '=', line.product_id.product_tmpl_id.id)]) #product to product template
                products.append(product_id.id)

        domain = {'product_ids': [('id', 'in', products)]}
        return {'domain': domain}

    # Lines
    @api.onchange('product_ids')
    def onchange_lines_ids(self):
        lines = []
        quality_question = self.env['qc.inspection.line']
        for product in self.product_ids:
            questions = quality_question.search(
                [('product_id', '=', product.id), ('trigger_time_ids', 'in', self.stock_picking_id.ids)])
            if questions:
                for line in questions:
                    lines.append(line.id)
        self.update({'inspection_lines':[(6, 0, lines)]})
    #

    @api.model
    def create(self, vals):
        lines = []
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('qc.inspection') or _('New')
        if 'product_ids' in vals:
            questions = self.env['qc.inspection.line'].search(
                [('product_id', 'in', vals['product_ids'][0][2]), ('trigger_time_ids', 'in', vals['stock_picking_id'])])
            if questions:
                for line in questions:
                    lines.append(line.id)
            vals['inspection_lines'] = [(6, 0, lines)]
        result = super(QcInspection, self).create(vals)
        return result

    @api.multi
    def unlink(self):
        for inspection in self:
            if inspection.auto_generated:
                raise exceptions.UserError(
                    _("You cannot remove an auto-generated inspection."))
            if inspection.state != 'draft':
                raise exceptions.UserError(
                    _("You cannot remove an inspection that is not in draft "
                      "state."))
        return super(QcInspection, self).unlink()

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def action_todo(self):
        self.write({'state': 'ready'})

    @api.multi
    def action_confirm(self):
        for inspection in self:
            for line in inspection.inspection_lines:
                if line.question_type == 'qualitative':
                    if not line.qualitative_value:
                        raise exceptions.UserError(
                            _("You should provide an answer for all "
                              "qualitative questions."))
                else:
                    if not line.uom_id:
                        raise exceptions.UserError(
                            _("You should provide a unit of measure for "
                              "quantitative questions."))
            if inspection.success:
                inspection.state = 'success'
            else:
                inspection.state = 'waiting'

    @api.multi
    def action_approve(self):
        for inspection in self:
            if inspection.success:
                inspection.state = 'success'
            else:
                inspection.state = 'failed'

    @api.multi
    def action_cancel(self):
        self.write({'state': 'canceled'})



