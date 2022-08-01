from odoo import  fields, models,_


class ProductionDocument(models.Model):
    _name = "equipement.document"
    _rec_name = 'titre'
    _description ="Documentation de léquipement"

    titre=fields.Char("Titre")
    document=fields.Binary("Document")
    description=fields.Char("Description du document")
    equipement_id=fields.Many2one(comodel_name='equipement.equipement')


