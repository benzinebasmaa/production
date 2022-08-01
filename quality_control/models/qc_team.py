from odoo import fields, models


class QcTeam(models.Model):
    _name = 'qc.team'
    _description = 'Quality control  Teams'

    name = fields.Char("Nom de l'équipe", required=True)
    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.user.company_id
                                 )
    member_ids = fields.Many2many(
        'res.users', string="Membres de l'équipe",domain="[('company_ids', 'in', company_id)]")

