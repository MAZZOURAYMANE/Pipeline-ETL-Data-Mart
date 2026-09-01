from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta

class Action(models.Model):
    _name = 'action'
    _description = "Action CRUI"

    name = fields.Char(string="Intitulé de l'action", required=True)
    partenaire_id = fields.Many2one('res.partner', string="Partenaire concerné", required=True)
    date_lancement = fields.Date(string="Date de lancement")
    date_retour = fields.Date(string="Date de retour")
    observation = fields.Text(string="Observations")
    delai_jours = fields.Integer(string="Délai (en jours)", help="Nombre de jours prévu pour réaliser l'action")
    dossier_id = fields.Many2one('dossier', string="Dossier lié")

    statut = fields.Selection([
        ('preparation', 'En cours de préparation'),
        ('signature', 'En cours de signature'),
        ('realise', 'Réalisé')
    ], string="Statut de l'action", default='preparation')

    # Contrôle de cohérence entre dates
    @api.constrains('date_lancement', 'date_retour')
    def _check_dates(self):
        for rec in self:
            if rec.date_lancement and rec.date_retour:
                if rec.date_retour < rec.date_lancement:
                    raise ValidationError("La date de retour doit être postérieure à la date de lancement.")
    duree_reelle = fields.Integer(
        string="Durée réelle (jours)",
        compute='_compute_duree_reelle',
        store=True
    )

    alerte_retard = fields.Boolean(
        string="Alerte : Action en retard",
        compute='_compute_duree_reelle',
        store=True
    )

    @api.depends('date_lancement', 'date_retour', 'delai_jours')
    def _compute_duree_reelle(self):
        for rec in self:
            if rec.date_lancement and rec.date_retour:
                delta = (rec.date_retour - rec.date_lancement).days
                rec.duree_reelle = delta
                rec.alerte_retard = delta > rec.delai_jours
            else:
                rec.duree_reelle = 0
                rec.alerte_retard = False