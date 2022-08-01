from odoo import api, fields, models, _
import time
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import qrcode
import base64
from io import BytesIO


class ProductionEquipementCategorie(models.Model):
    _description = "Catégorie d'équipement"
    _name = 'equipement.categorie'

    name = fields.Char('Catégorie', required=True, translate=True)
    equipement_ids = fields.Many2many('equipement.equipement',string='Equipement',ondelete="cascade")

class ProductionEquipement(models.Model):
    _name = 'equipement.equipement'
    _description = 'Equipement'
    _inherit = ['mail.thread']

    CRITICALITY_SELECTION = [
        ('0', 'Géneral'),
        ('1', 'Important'),
        ('2', 'Très important'),
        ('3', 'critique')
    ]

    ASSET_STATE = [
        ('fonctionnel', 'Fonctionnel'),
        ('enpanne', 'En panne'),
        ('maintenance', 'Maintenance'),
        ('miseaurebut', 'Mise au rebut')
    ]


    location_id = fields.Many2one('mrp.workcenter', "localisation",required=True)
    name = fields.Char("Nom de l'équipement", size=64, required=True, translate=True)
    maintenance_state = fields.Selection(ASSET_STATE,store="True",tracking=True,string="Etat de l'équipement",default='fonctionnel')
    criticality = fields.Selection(CRITICALITY_SELECTION, 'Criticité')
    user_id = fields.Many2one('res.users', 'Responsable', track_visibility='onchange')
    asset_number = fields.Char(string='N°équipement', required=True, copy=False, readonly=True,
                               index=True, default=lambda self: _('New'))
    investissement_number = fields.Char("N°interne", size=64)
    model = fields.Char('Modèle', size=64)
    serial = fields.Char('N°série', required=True, size=64)
    vendor = fields.Char('Fournisseur')
    manufacturer = fields.Char('Constructeur')
    Construction_date = fields.Date('Date de Construction',default=time.strftime('%Y-%m-%d'))
    start_date = fields.Datetime('Date de  Mise en service',default=time.strftime('%Y-%m-%d'))
    purchase_date = fields.Date("Date d'acquisition",default=time.strftime('%Y-%m-%d'))
    purchase_price = fields.Float("Valeur d'acquisition")
    Facture_number = fields.Char("N°Facture", size=64)
    designation=fields.Char("Description")
    facture_date = fields.Date("Date Facture")
    warranty_start_date = fields.Date('Début de la garantie')
    warranty_end_date = fields.Char('Durée de la garantie')
    image = fields.Binary("Image")
    image_small = fields.Binary("Small-sized image")
    image_medium = fields.Binary("Medium-sized image")
    category_ids = fields.Many2many('equipement.categorie',string='Catégorie',ondelete="cascade")
    marque_id = fields.Many2one('equipement.marque', string='Marque')
    #Composants
    composant_ids = fields.One2many('equipement.composants','equipement_id', string='Composants')
    #Donnée technique
    alimentation=fields.Char("Alimentation")
    puissance_maximale=fields.Char("Puissance Maximale")
    capacité=fields.Char("Capacité")
    vitesse=fields.Char("Vitesse")
    poids=fields.Char("Poids")
    dimention=fields.Char("Dimentions")
    Bruit_SELECTION = [
        ('0', '<85dB'),
        ('1', '>85dB')
    ]
    bruit=fields.Selection(Bruit_SELECTION,"Bruit")
    fréquence=fields.Char("Fréquence d'utilisation")
    detail=fields.Char(string=" ")
    #Document
    document_ids = fields.One2many('equipement.document', 'equipement_id', string='Documents')
    # employe
    employee_id = fields.Many2one('hr.employee', string="Attribuer à l'Employé", tracking=True)

    #QR code
    qr_code = fields.Binary(" ")

    def generate_qr(self):
        if self.name:
            if self.serial:
                if self.asset_number:
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data("Equipement")
                    qr.add_data('\n')
                    qr.add_data("Nom:")
                    qr.add_data(self.name)
                    qr.add_data('\n')
                    qr.add_data("N° Série:")
                    qr.add_data(self.serial)
                    qr.add_data('\n')
                    qr.add_data("N°équipement:")
                    qr.add_data(self.asset_number)
                    qr.make(fit=True)
                    img = qr.make_image()
                    tmp = BytesIO()
                    img.save(tmp, format="PNG")
                    qr_img = base64.b64encode(tmp.getvalue())
                    self.qr_code = qr_img
                else:
                    raise UserError(_("Vérifier si le nom , numéro de série ainsi que numéro d'équipement ne sont pas vide"))


    #Numéro séquentiel
    @api.model
    def create(self, vals):

        if vals.get('asset_number', _('New')) == _('New'):
                vals['asset_number'] = self.env['ir.sequence'].next_by_code('equipement.equipement.sequence') or _('New')

        result = super(ProductionEquipement, self).create(vals)
        return result

    #Date control
    @api.onchange('start_date','Construction_date','purchase_date')
    def check_date(self):
        cons = fields.Date.from_string(self.Construction_date)
        mise_enservice = fields.Date.from_string(self.start_date)
        acquis= fields.Date.from_string(self.purchase_date)
        if mise_enservice < cons:
            raise ValidationError(
                _("La date de mise en service doit etre supérieur ou égale à la date Date de Construction"))
        if acquis > mise_enservice:
            raise ValidationError(
                _("La date de mise en service doit etre supérieur ou égale à la date d'acquisition"))

    #State management

    def action_scrap(self):
        self.write({'maintenance_state': 'miseaurebut'})
        return True

    def action_fonctionnel(self):
        self.write({'maintenance_state': 'fonctionnel'})
        return True

    def action_en_panne(self):
        self.write({'maintenance_state': 'enpanne'})
        return True

    def action_maintenance(self):
        self.write({'maintenance_state': 'maintenance'})
        return True

    #Unlink
    def unlink(self):
        if (self.maintenance_state == 'enpanne' or self.maintenance_state =='maintenance'):
            raise UserError(_("Vous ne pouvez pas supprimez cet équipement avant de clôturer l'ordre de maintenance actuelle."))

        composant_to_delete = self.composant_ids
        if composant_to_delete:
            composant_to_delete.unlink()
        return super(ProductionEquipement, self).unlink()