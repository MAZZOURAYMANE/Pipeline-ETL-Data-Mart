from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo import models, fields, api


class Dossier(models.Model):
    _name = 'dossier'
    _description = "dossier d'investissment"
    # ELEMENT GENERAUX
    statut_dossier = fields.Selection([
        ('precrui', 'PRECRUI'),
        ('crui', 'CRUI'),
        ('postcrui', 'POSTCRUI'),
        ('suivi', 'SUIVI'),
    ], string="Statut du dossier",default="precrui")
    decision_dossier = fields.Char(
        string="Décision finale du dossier",
        compute="_compute_decision_dossier",
        store=True
    )

    # ELEMENT PRE CRUI
    projet_id = fields.Many2one('projet', string="Projet")
    dossier_id = fields.Integer(string='Dossier ID')
    reference = fields.Char(string="Reference")
    remarque_crui = fields.Text(string="remarque_crui")
    commission_id = fields.One2many('commission.crui', 'dossier_id', string="Commission")
    state = fields.Selection([
        ("en cours","en cours"),
        ("en retard","en retard"),
        ("traité","traité")
    ], string ="statut de traitement du dossier", default="en cours")
    actes_ids = fields.Many2many('act', string="Acts", widget="many2many")
    action_ids = fields.Many2many('action', string="Actions", widget="many2many")
    date_depot = fields.Datetime(string="Date de soumission par l'investisseur")
    date_retour_spoc = fields.Datetime(string="Date de validation par le conseiller")
    date_diffusion = fields.Datetime(string="Date de diffusion par le conseiller")
    observation_traitement_spoc = fields.Text(string="Observations sur traitement spoc")
    observation_spoc = fields.Text(string="Observation SPOC")
    etat_procedure = fields.Selection([
        ('En cours de dépôt', 'En cours de dépôt'),
        ('En attente administration', 'En attente administration'),
        ('Programmée', 'Programmée'),
        ('Complément', 'Complément'),
        ('Actions à réaliser', 'Actions à réaliser'),
        ('Clôturée', 'Clôturée')],
        string="Etat de la procédure")
    name = fields.Char(string="Intitulé")

    # ELEMENT CRUI
    date_passage = fields.Datetime(string="Date de Passage CRUI")
    decision_crui = fields.Selection([
        ('Avis favorable','Avis favorable'),
        ('Avis favorable sous réserve','Avis favorable sous réserve'),
        ('Complément','Complément'),
        ('Avis défavorable','Avis défavorable'),
        ('Reprogrammer','Reprogrammer'),
    ],string="Décisions CRUI")
    argument_crui = fields.Text(string="Argument CRUI")
    # ELEMENT RECOURS GRACIEUX
    date_depot_lettre_recours = fields.Datetime(string="Date dépot lettre de Recours")
    recours_wali = fields.Selection([
        ('Oui','Oui'),
        ('Non','Non')
    ],string="Recours Wali", default='Non')
    avis_wali = fields.Selection([
        ('Avis favorable','Avis favorable'),
        ('Avis favorable sous réserve','Avis favorable sous réserve'),
        ('Avis défavorable','Avis défavorable'),
    ],string="Avis du recours Wali")
    etat_decision_wali = fields.Selection([
        ('Maintien avis CRUI', 'Maintien avis CRUI'),
        ('Non Maintien', 'Non Maintien')
    ], string="Décision après recours gracieux", compute="_compute_etat_decision_wali", store=True)
    # ELEMENT RECOURS MINISTERIEL
    date_comite_ministeriel = fields.Datetime(string="Date du recours ministeriel")
    recours_comite_ministeriel = fields.Selection([
        ('Oui','Oui'),
        ('Non','Non')
    ],"Recours comité de pilotage", default='Non')
    avis_recours_ministeriel = fields.Selection([
        ('Avis favorable','Avis favorable'),
        ('Avis favorable sous réserve','Avis favorable sous réserve'),
        ('Avis défavorable','Avis défavorable'),
    ],string="Avis du recours ministriel")
    decision_comite_ministeriel = fields.Selection([
        ('Maintien avis CRUI', 'Maintien avis CRUI'),
        ('Non Maintien', 'Non Maintien')
    ], string="Décision recours Minitriel", compute="_compute_etat_decision_recour_ministeriel", store=True)
    
    # CAS FAVORABLE/FAVORABLE SOUS RESERVE
    #avant delivrance d'acte
    date_insertion = fields.Datetime(string="Date d'insertion PV signé")
    observation_post_crui = fields.Text(
    string="observations relatives au traitement retard levé réserves / délivrance actes")
    date_leve_reserve = fields.Datetime(string="Date de levé de réserve")
    
    #aprés delivrance d'acte
    date_delivrance = fields.Datetime(string="Date de Délivrance Acte")

     #Duplication Dossier
    def duplicate_selected_dossier(self, default=None):
        return super(Dossier,self).copy(default)
    def write(self,vals):
        print(vals)
        return super(Dossier,self).write(vals)

    @api.constrains('date_depot', 'date_retour_spoc', 'date_diffusion', 'date_passage')
    def _check_dates(self):
        for record in self:
            if record.date_depot and record.date_retour_spoc:
                if record.date_retour_spoc < record.date_depot:
                    raise ValidationError("La date de retour SPOC doit être postérieure à la date de dépôt.")
            if record.date_retour_spoc and record.date_diffusion:
                if record.date_diffusion < record.date_retour_spoc:
                    raise ValidationError("La date de diffusion doit être postérieure à la date de retour SPOC.")
            if record.date_diffusion and record.date_passage:
                if record.date_passage < record.date_diffusion:
                    raise ValidationError("La date de passage CRUI doit être postérieure à la date de diffusion.")
            # Contrôles croisés si une étape intermédiaire est ignorée
            if record.date_depot and record.date_diffusion:
                if record.date_diffusion < record.date_depot:
                    raise ValidationError("La date de diffusion doit être postérieure à la date de dépôt.")
            if record.date_depot and record.date_passage:
                if record.date_passage < record.date_depot:
                    raise ValidationError("La date de passage CRUI doit être postérieure à la date de dépôt.")
            # Blocage si la date de passage est saisie sans la date de diffusion
            if record.date_passage and not record.date_diffusion:
                raise ValidationError("La date de passage CRUI ne peut être renseignée que si la date de diffusion est définie.")
    @api.onchange('date_depot_lettre_recours')
    def _onchange_date_depot_lettre_recours(self):
        """Met automatiquement 'Oui' dans recours_wali si date_depot_lettre_recours est remplie."""
        if self.date_depot_lettre_recours:
            self.recours_wali = 'Oui'
        else:
            self.recours_wali = 'Non'
    @api.depends('avis_wali', 'decision_crui')
    def _compute_etat_decision_wali(self):
        """Définit 'Maintien avis CRUI' si avis_wali == decision_crui, sinon 'Recommandation'."""
        for record in self:
            if record.avis_wali and record.decision_crui:
                if record.avis_wali == record.decision_crui:
                    record.etat_decision_wali = 'Maintien avis CRUI'
                else:
                    record.etat_decision_wali = 'Non Maintien'
            else:
                record.etat_decision_wali = False  # Valeur vide si
    @api.onchange('date_comite_ministeriel')
    def _onchange_date_comite_ministeriel(self):
        """Met automatiquement 'Oui' dans recours_comite_ministeriel si date_comite_ministeriel est remplie."""
        if self.date_comite_ministeriel:
            self.recours_comite_ministeriel = 'Oui'
        else:
            self.recours_comite_ministeriel = 'Non'
    
    @api.depends('avis_recours_ministeriel', 'decision_crui')
    def _compute_etat_decision_recour_ministeriel(self):
        """Définit 'Maintien avis CRUI' si avis_recours_ministeriel == decision_crui, sinon 'Recommandation'."""
        for record in self:
            if record.avis_recours_ministeriel and record.decision_crui:
                if record.avis_recours_ministeriel == record.decision_crui:
                    record.decision_comite_ministeriel = 'Maintien avis CRUI'
                else:
                    record.decision_comite_ministeriel = 'Non Maintien'
            else:
                record.decision_comite_ministeriel = False  # Valeur vide si

    # ELEMENT KPI
    annee = fields.Integer(
    string="Année",
    compute="_compute_annee",
    store=True
    )
    @api.depends('date_depot')
    def _compute_annee(self):
        """ Récupérer l'année du dépôt du dossier """
        for rec in self:
            rec.annee = rec.date_depot.year if rec.date_depot else False

     # INDICATEUR 1
    delai_moyen_traitement = fields.Integer(
        string="Le délai moyen de traitement d’un dossier d’investissement complet déposé auprès du Centre Régional d’Investissement et de sa soumission à la Commission Régionale Unifiée d’Investissement .",
        compute='_compute_delai_moyen_traitement',
        store=True
        )
    @api.depends('date_diffusion', 'date_depot')
    def _compute_delai_moyen_traitement(self):
        for record in self:
            if record.date_diffusion and record.date_depot:
                current_date = record.date_depot
                end_date = record.date_diffusion
                working_days = 0

                while current_date <= end_date:
                    # Vérifier si le jour est un jour ouvré (lundi à vendredi)
                    if current_date.weekday() < 5:  
                        working_days += 1
                    current_date += timedelta(days=1)

                record.delai_moyen_traitement = working_days - 1  # Exclure le jour de dépôt
            else:
                record.delai_moyen_traitement = 0

    # INDICATEUR 2
    soumis_30j = fields.Boolean(
        string="Soumis à la CRUI en ≤ 30 jours",
        compute="_compute_soumis_30j",
        store=True
    )
    @api.depends('date_depot', 'date_diffusion')
    def _compute_soumis_30j(self):
        """ Vérifie si le dossier a été traité en ≤ 30 jours après sa date de dépôt """
        for rec in self:
            if rec.date_depot and rec.date_diffusion:
                rec.soumis_30j = (rec.date_diffusion - rec.date_depot).days <= 30
            else:
                rec.soumis_30j = False
    #INDICATEUR 3
    delai_examen_crui = fields.Integer(
    string="INDICATEUR 3: Le délai moyen d’examen et de prise de décision concernant les dossiers d’investissement par la CRUI",
    compute="_compute_delai_examen_crui",
    store=True
    )
    @api.depends('date_depot', 'date_passage', 'decision_crui')
    def _compute_delai_examen_crui(self):
        """ Calcule le délai d'examen par la CRUI en jours ouvrés seulement si une décision CRUI est renseignée """
        for rec in self:
            if rec.date_depot and rec.date_passage and rec.decision_crui:
                current_date = rec.date_depot
                end_date = rec.date_passage
                working_days = 0

                while current_date <= end_date:
                    if current_date.weekday() < 5:  # Exclure les week-ends
                        working_days += 1
                    current_date += timedelta(days=1)

                rec.delai_examen_crui = working_days - 1  # Exclure le jour de dépôt
            else:
                rec.delai_examen_crui = 0
    #INDICATEUR 4
    examine_30j = fields.Boolean(
        string="Examiné en ≤ 30 jours",
        compute="_compute_examine_30j",
        store=True
    )
    @api.depends('date_diffusion', 'date_passage', 'decision_crui')
    def _compute_examine_30j(self):
        """ Vérifie si le dossier a été examiné en ≤ 30 jours après la date de diffusion,
            uniquement si une décision CRUI finale a été rendue """
        decisions_valides = ['Avis favorable', 'Avis favorable sous réserve', 'Avis défavorable']
        
        for rec in self:
            if rec.date_diffusion and rec.date_passage and rec.decision_crui in decisions_valides:
                delai = (rec.date_passage - rec.date_diffusion).days
                rec.examine_30j = delai <= 30
            else:
                rec.examine_30j = False
    #INDICATEUR 5
    approuve_crui = fields.Boolean(
        string="Approuvé par la CRUI",
        compute="_compute_approuve_crui",
        store=True
    )
    @api.depends('decision_crui')
    def _compute_approuve_crui(self):
        """ Vérifie si le dossier a reçu un avis favorable """
        for rec in self:
            rec.approuve_crui = rec.decision_crui == 'Avis favorable'
    
    #Indicateur 6   NON APPLICABLE LE MONTANT d'INVESTISSMENT CONCERNE SUR LES PROJETS
    #Indicateur 7   NON APPLICABLE LE MONTANT d'INVESTISSMENT CONCERNE SUR LES PROJETS
    
    #Indicateur 8   NON APPLICABLE RATIO MONTANT INVESTISSEMENT LES PROJETS
    #Indicateur 9   NON APPLICABLE RATION NOMBRE EMPLOI CONCERNE  LES PROJETS
    #indicateur 10  Délai délivrance acte
    delai_delivrance_act = fields.Integer(
        string="Délai délivrance acte",
        compute='_compute_delai_delivrance_act', store=True)
    @api.depends('date_passage', 'date_delivrance')
    def _compute_delai_delivrance_act(self):
        working_days = 0

        for record in self:
            current_date = record.date_passage
            end_date = record.date_delivrance
            if record.date_passage and record.date_delivrance:
                while current_date <= end_date:
                    # Check if the current date is a weekday (Monday to Friday) and not a holiday
                    if current_date.weekday() < 5:
                        working_days += 1

                    # Move to the next day
                    current_date += timedelta(days=1)
                    record.delai_delivrance_act = working_days - 1
            else:
                record.delai_delivrance_act = working_days - 1
    #indicateur 11  Délai délivrance acte
    delai_total_traitement_dossier = fields.Integer(
        string="Délai total de traitement dossier",
        compute='_compute_delai_total_traitement_dossier', store=True)
   
    @api.depends('date_depot', 'date_delivrance')
    def _compute_delai_total_traitement_dossier(self):
        working_days = 0

        for record in self:
            current_date = record.date_depot
            end_date = record.date_delivrance
            if record.date_depot and record.date_delivrance:
                while current_date <= end_date:
                    # Check if the current date is a weekday (Monday to Friday) and not a holiday
                    if current_date.weekday() < 5:
                        working_days += 1

                    # Move to the next day
                    current_date += timedelta(days=1)
                    record.delai_total_traitement_dossier = working_days - 1
            else:
                record.delai_total_traitement_dossier = working_days - 1



    delai_instruction_CRUI = fields.Integer(string="Délai instruction CRUI dernière date",
                                           compute='_compute_delai_instruction_CRUI', store=True)
    @api.depends('date_diffusion', 'date_passage')
    def _compute_delai_instruction_CRUI(self):
        working_days = 0

        for record in self:
            current_date = record.date_diffusion
            end_date = record.date_passage
            if record.date_diffusion and record.date_passage:
                while current_date <= end_date:
                    # Check if the current date is a weekday (Monday to Friday) and not a holiday
                    if current_date.weekday() < 5:
                        working_days += 1

                    # Move to the next day
                    current_date += timedelta(days=1)
                    record.delai_instruction_CRUI = working_days - 1
            else:
                record.delai_instruction_CRUI = working_days - 1

    delai_instruction_CRUI_dossier_sature = fields.Integer(string="Délai instruction CRUI dernière date (dossiers statués)",
                                            compute='_compute_delai_instruction_CRUI_dossier_staure', store=True)
    @api.depends('date_depot', 'date_passage')
    def _compute_delai_instruction_CRUI_dossier_staure(self):
        working_days = 0

        for record in self:
            current_date = record.date_depot
            end_date = record.date_passage
            if record.date_depot and record.date_passage:
                while current_date <= end_date:
                    # Check if the current date is a weekday (Monday to Friday) and not a holiday
                    if current_date.weekday() < 5:
                        working_days += 1

                    # Move to the next day
                    current_date += timedelta(days=1)
                    record.delai_instruction_CRUI_dossier_sature = working_days - 1
            else:
                record.delai_instruction_CRUI_dossier_sature = working_days - 1
    @api.depends('avis_recours_ministeriel', 'avis_wali', 'decision_crui')
    def _compute_decision_dossier(self):
        for record in self:
            if record.avis_recours_ministeriel:
                record.decision_dossier = record.avis_recours_ministeriel
            elif record.avis_wali:
                record.decision_dossier = record.avis_wali
            else:
                record.decision_dossier = record.decision_crui