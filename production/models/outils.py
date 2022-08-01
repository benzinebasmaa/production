from odoo import api, fields, models,_


class ProductionOutils(models.Model):
    _name = "equipement.outils"
    _rec_name = 'nom'
    _description = 'Outils de maintenance'

    image= fields.Binary("Image")
    nom = fields.Char(string="Nom de l'outils", required=True)
    Outils_number= fields.Char(string='N°outils', required=True, copy=False,readonly=True,
                               index=True, default=lambda self: _('New'))
    purchase_price = fields.Float("Prix d'achat")
    cout = fields.Float("Cout")
    quantité_stock = fields.Float("Quantité en stock")
    quantité_prévu = fields.Float("Quantité prévu")
    composants_ids = fields.Many2many('equipement.composants',string='Composants')

    @api.model
    def create(self,vals):

        if vals.get('Outils_number', _('New')) == _('New'):
                vals['Outils_number'] = self.env['ir.sequence'].next_by_code('equipement.outils.sequence') or _('New')

        result = super(ProductionOutils, self).create(vals)
        return result

