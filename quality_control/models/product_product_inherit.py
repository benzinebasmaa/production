from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"


    test_lines_ids = fields.One2many(
        comodel_name='qc.inspection.line', inverse_name='product_product_id',
        string='Questions', copy=True)
