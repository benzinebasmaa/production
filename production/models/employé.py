from odoo import api, models, fields,_

class Employee(models.Model):
    _inherit = 'hr.employee'


    equipement_ids=fields.One2many('equipement.equipement','employee_id')
    equipment_count = fields.Integer('Equipments', compute='_compute_equipment_count')

    @api.depends('equipement_ids')
    def _compute_equipment_count(self):
        for employee in self:
            employee.equipment_count = len(employee.equipement_ids)

    def action_view_asset(self):
        return {
            'name': _('Equipement'),
            'view_mode': 'tree,form',
            'res_model': 'equipement.equipement',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('employee_id','=', self.id)],

        }




