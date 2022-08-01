from odoo import fields, models, _


class QcTestQuestionValue(models.Model):
    _name = 'qc.test.question.value'
    _description = 'Possible values for qualitative questions.'

    test_line = fields.Many2one(
        comodel_name="qc.inspection.line", string="Test question")
    name = fields.Char(
        string='Name', required=True, translate=True)
    ok = fields.Boolean(
        string='Correct answer?',
        help="When this field is marked, the answer is considered correct.")
