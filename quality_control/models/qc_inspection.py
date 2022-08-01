from odoo import api, exceptions, fields, models, _
from odoo.tools import formatLang
import odoo.addons.decimal_precision as dp


class QcInspection(models.Model):
    _name = 'qc.inspection'
    _description = 'Quality control inspection'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.depends('inspection_lines', 'inspection_lines.success')
    def _compute_success(self):
        for i in self:
            i.success = all([x.success for x in i.inspection_lines])

    name = fields.Char(
        string='Inspection number', required=True, default=lambda self: _('New'),
        readonly=True, states={'draft': [('readonly', False)]}, copy=False, )

    date = fields.Datetime(
        string='Date', required=True, readonly=True, copy=False,
        default=fields.Datetime.now,
        states={'draft': [('readonly', False)]})

    product_id = fields.Many2one(
        comodel_name="product.product",
        store=True, help="Product associated with the inspection",
        oldname='product')
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
        compute="_compute_success", string='Success',
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
        comodel_name='qc.test.category', string='Category')

    team_ids = fields.Many2many('qc.team', string='Teams')

    stock_picking_id = fields.Many2one('stock.picking.type', string='Opération', required=True)
    picking_ids = fields.Many2many('stock.picking', string='Source Operation',
                                   domain="[('picking_type_id','=',stock_picking_id)]", )
    operation_ids = fields.Many2many('mrp.production', string='Source Operation')

    @api.model
    def create(self, vals):

        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('qc.inspection') or _('New')

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


class QcInspectionLine(models.Model):
    _name = 'qc.inspection.line'
    _description = "Quality control inspection line"
    _order = 'sequence, id'

    @api.depends('question_type', 'uom_id', 'test_uom_id', 'max_value',
                 'min_value', 'quantitative_value', 'qualitative_value',
                 'possible_ql_values')
    def _compute_quality_test_check(self):
        for l in self:
            if l.question_type == 'qualitative':
                l.success = l.qualitative_value.ok
            else:
                if l.uom_id.id == l.test_uom_id.id:
                    amount = l.quantitative_value
                else:
                    amount = self.env['product.uom']._compute_quantity(
                        l.quantitative_value,
                        l.test_uom_id.id)
                l.success = l.max_value >= amount >= l.min_value

    @api.depends('possible_ql_values', 'min_value', 'max_value', 'test_uom_id',
                 'question_type')
    def _compute_valid_values(self):
        for l in self:
            if l.question_type == 'qualitative':
                l.valid_values = \
                    ", ".join([x.name for x in l.possible_ql_values if x.ok])
            else:
                l.valid_values = "%s ~ %s" % (
                    formatLang(self.env, l.min_value),
                    formatLang(self.env, l.max_value))
                if self.env.ref("product.group_uom") \
                        in self.env.user.groups_id:
                    l.valid_values += " %s" % l.test_uom_id.name


    @api.constrains('ql_values')
    def _check_valid_answers(self):
        for tc in self:
            if (tc.question_type == 'qualitative' and tc.ql_values and
                    not tc.ql_values.filtered('ok')):
                raise exceptions.ValidationError(
                    _("Question '%s' is not valid: "
                      "you have to mark at least one value as OK.")
                    % tc.name_get()[0][1])

    @api.constrains('min_value', 'max_value')
    def _check_valid_range(self):
        for tc in self:
            if tc.question_type == 'quantitative' and tc.min_value > tc.max_value:
                raise exceptions.ValidationError(
                    _("Question '%s' is not valid: "
                      "minimum value can't be higher than maximum value.")
                    % tc.name_get()[0][1])

    trigger_time_ids = fields.Many2many('stock.picking.type', string='Trigger On',required= True)

    inspection_id = fields.Many2one(
        comodel_name='qc.inspection', string='Inspection', ondelete='cascade')

    name = fields.Char(string="Question",required=True)

    product_id = fields.Many2one(
        comodel_name="product.template",
        store=True, oldname='product')

    possible_ql_values = fields.Many2many(
        comodel_name='qc.test.question.value', string='Answers')


    ql_values = fields.One2many(
        comodel_name='qc.test.question.value', inverse_name="test_line",
        string='Qualitative values', copy=True)

    sequence = fields.Integer(
        string='Sequence', required=True, default="10")

    quantitative_value = fields.Float(
        'Quantitative value', digits=dp.get_precision('Quality Control'),
        help="Value of the result for a quantitative question.")
    qualitative_value = fields.Many2one(
        comodel_name='qc.test.question.value', string='Qualitative value',
        help="Value of the result for a qualitative question.",
        domain="[('id', 'in', possible_ql_values)]")
    notes = fields.Text(string='Notes')
    min_value = fields.Float(
        string='Min', digits=dp.get_precision('Quality Control'),
         help="Minimum valid value for a quantitative question.")
    max_value = fields.Float(
        string='Max', digits=dp.get_precision('Quality Control'),
         help="Maximum valid value for a quantitative question.")
    test_uom_id = fields.Many2one(
        comodel_name='product.uom', string='Test UoM', readonly=True,
        help="UoM for minimum and maximum values for a quantitative "
             "question.")
    test_uom_category = fields.Many2one(
        comodel_name="product.uom.categ", related="test_uom_id.category_id",
        store=True)
    uom_id = fields.Many2one(
        comodel_name='product.uom', string='UoM',
        help="UoM of the inspection value for a quantitative question.")
    question_type = fields.Selection(
        [('qualitative', 'Qualitative'),
         ('quantitative', 'Quantitative')],
        string='Question type',required=True)
    valid_values = fields.Char(string="Valid values", store=True,
                               compute="_compute_valid_values")
    success = fields.Boolean(
        compute="_compute_quality_test_check", string="Success?", store=True)
