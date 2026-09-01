from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _


class Soumission(models.Model):
    _name = 'soumission'
    _description = "gestion des soumission"
    dossier_id = fields.Integer(string='Dossier ID')
    projet_id = fields.Many2one('projet', string="Projet")
    state = fields.Selection([
        ("en cours","en cours"),
        ("en retard","en retard"),
        ("traité","traité")
    ], string ="statut de traitement du dossier", default="en cours")
    
    actes_ids = fields.Many2many('act', string="Acts", widget="many2many")
    name = fields.Char(string="Intitulé")
    reference = fields.Char(string="Reference")
    date_depot = fields.Datetime(string="Date de soumission par l'investisseur")
    date_retour_spoc = fields.Datetime(string="Date Retrour SPOC")
    date_diffusion = fields.Datetime(string="Date Diffusion Dossier")
    delai_reactivite_spoc = fields.Integer(string="Délai réactivité SPOC (en jours ouvrés)",compute='_compute_delai_reactivite_spoc', store=True)
    statut_dossier = fields.Selection([
        ('precrui', 'precrui'),
        ('crui', 'crui'),
        ('postcrui', 'postcrui'),
    ], string="Statut du dossier",default="precrui")
    
    observation_spoc = fields.Text(string="Observation SPOC")
    observation_traitement_spoc = fields.Text(string="Observations sur traitement spoc")
    
    annee = fields.Integer(
        string="Année",
        compute="_compute_annee",
        store=True
    )
    etat_procedure = fields.Selection([
        ('En cours de dépôt', 'En cours de dépôt'),
        ('En attente administration', 'En attente administration'),
        ('Programmée', 'Programmée'),
        ('Complément', 'Complément'),
        ('Actions à réaliser', 'Actions à réaliser'),
        ('Clôturée', 'Clôturée')],
        string="Etat de la procédure")
    @api.depends('date_depot', 'date_retour_spoc')
    def _compute_delai_reactivite_spoc(self):
        working_days = 0

        for record in self:
            current_date = record.date_depot
            end_date = record.date_retour_spoc
            if record.date_depot and record.date_retour_spoc:
                while current_date <= end_date:
                    # Check if the current date is a weekday (Monday to Friday) and not a holiday
                    if current_date.weekday() < 5:
                        working_days += 1

                    # Move to the next day
                    current_date += timedelta(days=1)
                    record.delai_reactivite_spoc = working_days-1
            else:
                record.delai_reactivite_spoc = working_days-1
    @api.depends('date_depot')
    def _compute_annee(self):
        """ Récupérer l'année du dépôt du dossier """
        for rec in self:
            rec.annee = rec.date_depot.year if rec.date_depot else False

    @api.constrains('date_depot', 'date_retour_spoc')
    def _check_date_retour_spoc_after_date_depot(self):
        for record in self:
            if (
                record.date_depot
                and record.date_retour_spoc
                and record.date_retour_spoc <= record.date_depot
            ):
                raise ValidationError(
                    _("La date de retour SPOC doit être strictement supérieure à la date de dépôt.")
                )

    def duplicate_selected_soumission(self, default=None):
        return super(Soumission,self).copy(default)

    def action_check_and_fix_dates(self):
        soumissions = self.env['soumission'].search([
            ('date_depot', '!=', False),
            ('date_retour_spoc', '!=', False),
        ])
        invalid_soumissions = soumissions.filtered(
            lambda s: s.date_retour_spoc <= s.date_depot
        )

        for soumission in invalid_soumissions:
            soumission.write({
                'date_retour_spoc': soumission.date_depot + timedelta(minutes=5)
            })

        message = _(
            "%s soumission(s) corrigée(s)."
        ) % len(invalid_soumissions) if invalid_soumissions else _(
            "Aucune soumission invalide trouvée."
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Vérification des soumissions"),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_diffuser(self):
        self.ensure_one()

        # Renseigner la date de diffusion si elle n'est pas déjà définie
        if not self.date_diffusion:
            self.date_diffusion = fields.Datetime.now()

        # Créer un dossier
        dossier = self.env['dossier'].create({
            'projet_id': self.projet_id.id,
            'dossier_id': self.dossier_id,
            'name': self.name,
            'statut_dossier': self.statut_dossier,
            'date_depot': self.date_depot,
            'date_retour_spoc': self.date_retour_spoc,
            'date_diffusion': self.date_diffusion,
            'reference': self.reference,
            'actes_ids': [(6, 0, self.actes_ids.ids)],
            'etat_procedure': self.etat_procedure,
            'observation_traitement_spoc': self.observation_traitement_spoc,
            'observation_spoc': self.observation_spoc,
        })

        # Marquer la soumission comme traitée
        self.state = 'traité'

        # Ouvre le formulaire de création de la commission
        return {
            'type': 'ir.actions.act_window',
            'name': 'Créer la Commission',
            'res_model': 'commission.crui',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': f"Commission {self.projet_id.name or ''}",
                'default_dossier_id': dossier.id,
                # ne pas mettre default_date_passage ici pour laisser l'utilisateur le saisir
            },
        }
