from odoo import  fields, models

class ProductionMarque(models.Model):
    _name = "equipement.marque"
    _rec_name = 'nom'
    _description = 'Marque des équipements'


    nom = fields.Char(string='Marque', required=True)
    equipement_ids = fields.One2many('equipement.equipement', 'marque_id', string='Equipement')