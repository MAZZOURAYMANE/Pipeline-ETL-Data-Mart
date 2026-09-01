from odoo import models, fields, api


class Visite(models.Model):
    _name = 'visite'
    _description = 'visite usagers'

    
    date_de_la_visite = fields.Datetime(string='Date de la visite')
    investisseur_id = fields.Many2one('res.partner', string="Investisseur")
    investisseur = fields.Char(string="Dénomination/nom et prénom", related="investisseur_id.name")
    telephone = fields.Char(string="Téléphone",related=  "investisseur_id.phone")
    adresse = fields.Char(string="Adresse",related=  "investisseur_id.street")
    email = fields.Char(string="Email",related=  "investisseur_id.email")
    #nationalite = fields.Char(string="Nationalité",related=  "investisseur_id.country")
    is_company = fields.Boolean(string='Fonction',related="investisseur_id.is_company")
    civilite = fields.Many2one('res.partner.title', string="Civilité", related="investisseur_id.title")
    prise_de_connaissance = fields.Char(string="Comment Avez-vous connu notre établissement")
    localisation = fields.Char(string="Localisation du projet")
    prefecture_id = fields.Many2one('prefecture',string='Province ou Préfecture')
    Objet = fields.Text(string="Objet de la visite ")
    suite = fields.Selection([
        ('', ''),
        ('Explications fournies','Explications fournies'),
        ('Information communiquée','Information communiquée'),


    ],string="Suite Donnée")
    type_visite = fields.Selection([
        ('', ''),
        ('Pré-inscruction CRUI','Pré-inscruction CRUI'),
        ('Visite/rendez-vous','Visite/rendez-vous'),


    ],string="Type de la visite")
    secteur = fields.Many2many('secteur', string="Secteur d’activité", widget="many2many")
    employe_id = fields.Many2one('hr.employee', string="Reçu par")
    recu_par = fields.Char(string="Employé", related="employe_id.name")
    department_id = fields.Many2one('hr.department', string="Orienter à une autre division")

    