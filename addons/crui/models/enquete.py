from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo import models, fields, api


class Enquete(models.Model):
    _name = 'enquete'
    _description = "Enquête de suivi"
    
    # ELEMENT SUIVIS
    date_suivi_effectue = fields.Datetime(string="Date de Suivi à effectuer (après délivrance tous actes)")
    etat_avancement = fields.Selection([
        ('En cours dautorisation','En cours dautorisation'),
        ('Autorisé / Travaux non entamés','Autorisé / Travaux non entamés'),
        ('Travaux en cours gros œuvres','Travaux en cours gros œuvres'),
        ('Travaux en cours finition','Travaux en cours finition'),
        ('Travaux achevés activité non démarrée','Travaux achevés activité non démarrée'),
        ('Travaux achevés activité démarrée','Travaux achevés activité démarrée')
    ],string="Etat d'avancement projet")
    date_autorisation = fields.Datetime(string="Date obtention autorisation de construire")
    date_lancement_effective = fields.Datetime(string="date effective lancement travaux")
    date_fin_travaux = fields.Datetime(string="Date fin travaux (mois/année)")
    date_demarage_activite = fields.Datetime(string="Date démarrage d'activité (mois/année)")
    pourcentage_realisation = fields.Float(string="pourcentage état avancement")
    montant_investissement_reel = fields.Float(string="MT d'investissement réalisé")
    nombre_emplois_reel = fields.Integer(string="nombre d'emplois créés")
    observation_suivi = fields.Char(string="Observation (projet  abondonné/ en stand by …)")
    projet_id = fields.Many2one('projet', string="Projet")
