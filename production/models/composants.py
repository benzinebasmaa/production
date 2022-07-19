from odoo import api, fields, models, _


class ProductionComposant(models.Model):
    _name = "equipement.composants"
    _description = "Composants de l'équipement"
    _rec_name = 'nom'

    CRITICALITY_SELECTION = [
        ('0', 'Géneral'),
        ('1', 'Important'),
        ('2', 'Très important'),
        ('3', 'critique')
    ]
    #Composant parent
    @api.onchange('equipement_id')
    def onchange_composant_ids(self):
        for rec in self :
            domain = {'parent_id': [('equipement_id', '=', rec.equipement_id.id)]}
            return {'domain': domain}

    equipement_id = fields.Many2one(comodel_name='equipement.equipement', string='Equipement', required=True,domain="[('maintenance_state', '!=','miseaurebut')]")
    nom = fields.Char(string="Nom", required=True)
    criticality = fields.Selection(CRITICALITY_SELECTION, 'Criticité')
    composant_number = fields.Char(string='N°Composant', required=True, copy=False, readonly=True,
                                   index=True, default=lambda self: _('New'))
    marque_id = fields.Many2one(comodel_name='equipement.marque', string='Marque')
    description = fields.Char(string="Description")
    outils_ids = fields.Many2many('equipement.outils', string='Outils')

    # Hiararchy Composant & sous-composant
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = "nom"
    _rec_name = 'display_name'

    parent_id = fields.Many2one(
        "equipement.composants",
        "Composant parent",
        index=True,
        ondelete="cascade",
        track_visibility="onchange",
    )
    reference = fields.Char('Reference sous-composant')
    parent = fields.Boolean('Est un Parent', default=True)
    have_parent = fields.Boolean('A un Parent', default=True)
    child_ids = fields.One2many(
        "equipement.composants", "parent_id", "Sous-composants"
    )
    parent_left = fields.Integer("Left Parent", index=1)
    parent_right = fields.Integer("Right Parent", index=1)
    child_count = fields.Integer(
        compute="_compute_child_count", string="Nombre de sous-composants"
    )
    display_name = fields.Char(compute="_compute_display_name", string="Sous-composants")
    complete_name = fields.Char(compute="_compute_complete_name", store=True)
    parent_path = fields.Char(index=True)

    def name_get(self):
        return [(equipment.id, equipment.complete_name) for equipment in self]

    @api.depends("child_ids")
    def _compute_child_count(self):
        for equipment in self:
            equipment.child_count = len(equipment.child_ids)

    def _compute_display_name(self):
        for equipment in self:
            equipment.display_name = equipment.nom

    @api.depends("nom", "parent_id.complete_name")  # recursive definition
    def _compute_complete_name(self):
        for equipment in self:
            if equipment.parent_id:
                parent_name = equipment.parent_id.complete_name
                equipment.complete_name = parent_name + " / " + equipment.nom
            else:
                equipment.complete_name = equipment.nom

    def preview_child_list(self):
        return {
            "nom": _("Child equipment of %s") % self.nom,
            "type": "ir.actions.act_window",
            "res_model": "equipement.composants",
            "res_id": self.id,
            "view_mode": "list,form",
            "context": {
                **self.env.context,
                "default_parent_id": self.id,
                "parent_id_editable": False,
            },
            "domain": [("parent_id", "=", self.id)],
        }
    # Numéro sequen composant
    @api.model
    def create(self, vals):
        if vals.get('composant_number', _('New')) == _('New'):
            vals['composant_number'] = self.env['ir.sequence'].next_by_code('equipement.composants.sequence') or _('New')

        result = super(ProductionComposant, self).create(vals)
        return result

