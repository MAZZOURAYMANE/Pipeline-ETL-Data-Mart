from odoo import models, fields, api
class ProjetGlobalKPI(models.Model):
    _name = 'etat.bilan.projet'
    _description = 'Indicateurs globaux des projets'

    annee = fields.Integer(string="Année", required=True)
    def action_generer_bilan_annuel(self):
        """
        Action manuelle déclenchée par bouton
        """
        self.generate_annee_bilan_records()

    @api.model
    def generate_annee_bilan_records(self):
        """
        Pour chaque année détectée dans 'dossier',
        on crée (ou on laisse tel quel s'il existe déjà)
        un enregistrement dans 'etat.bilan.projet'.
        """
        # Récupérer la liste des années présentes dans 'dossier'
        projet_years = self.env['projet'].search([]).mapped('annee')
        unique_years = set(projet_years)  # On évite les doublons

        for year in unique_years:
            if year:  # ignorer les dossiers sans année
                bilan = self.search([('annee', '=', year)], limit=1)
                if not bilan:
                    # Créer l'enregistrement s'il n'existe pas
                    self.create({'annee': year})
                # Si le bilan existe déjà, on ne fait rien,
                # car les champs calculés se mettront à jour automatiquement
    # Exemple de champ calculé: nombre de dossiers favorables
    nb_dossiers_favorables = fields.Integer(
        string="Dossiers favorables",
        compute='_compute_nb_dossiers_favorables',
        store=True
    )
    nb_dossiers_favorables_sous_reserve = fields.Integer(
        string="Dossiers favorables sous résérves",
        compute='_compute_nb_dossiers_favorables_sous_reserve',
        store=True
    )
    nb_dossiers_defavorables = fields.Integer(
        string="Dossiers Défavorables",
        compute='_compute_nb_dossiers_defavorables',
        store=True
    )
    # Vous pouvez rajouter d'autres champs calculés pour la vue pivot
    # par exemple:
    nb_dossiers_complement = fields.Integer(
        string="Dossier avec demande de complément",
        compute='_compute_nb_dossiers_complement',
        store=True
    )
    nb_dossiers_reprogrammes = fields.Integer(
        string="Dossiers reprogrammés",
        compute='_compute_nb_dossiers_reprogrammes',
        store=True
    )
    # etc.
    @api.model
    def generate_annee_bilan_records(self):
        """
        Pour chaque année détectée dans 'dossier',
        on crée (ou on laisse tel quel s'il existe déjà)
        un enregistrement dans 'etat.bilan.projet'.
        """
        # Récupérer la liste des années présentes dans 'dossier'
        dossier_years = self.env['projet'].search([]).mapped('annee')
        unique_years = set(dossier_years)  # on évite les doublons

        for year in unique_years:
            if year:  # ignorer les dossiers sans année
                bilan = self.search([('annee', '=', year)], limit=1)
                if not bilan:
                    # Créer l'enregistrement s'il n'existe pas
                    self.create({'annee': year})
                # Si le bilan existe déjà, on ne fait rien,
                # car les champs calculés se mettront à jour automatiquement

    @api.depends('annee')
    def _compute_nb_dossiers_favorables(self):
        """
        Compte le nombre de dossiers dont la decision_projet == 'Avis favorable'
        pour l'année concernée.
        """
        for record in self:
            if record.annee:
                # On cherche dans le modèle dossier
                # en prenant uniquement ceux dont le champ annee == record.annee
                # et la decision_projet == 'Avis favorable'
                domain = [
                    ('annee', '=', record.annee),
                    ('decision_projet', '=', 'Avis favorable')
                ]
                count = self.env['projet'].search_count(domain)
                record.nb_dossiers_favorables = count
            else:
                record.nb_dossiers_favorables = 0
    @api.depends('annee')
    def _compute_nb_dossiers_favorables_sous_reserve(self):
        """
        Compte le nombre de dossiers dont la decision_projet == 'Avis favorable sous réserve'
        pour l'année concernée.
        """
        for record in self:
            if record.annee:
                # On cherche dans le modèle dossier
                # en prenant uniquement ceux dont le champ annee == record.annee
                # et la decision_projet == 'Avis favorable'
                domain = [
                    ('annee', '=', record.annee),
                    ('decision_projet', '=', 'Avis favorable sous réserve')
                ]
                count = self.env['projet'].search_count(domain)
                record.nb_dossiers_favorables_sous_reserve = count
            else:
                record.nb_dossiers_favorables_sous_reserve = 0
    @api.depends('annee')
    def _compute_nb_dossiers_defavorables(self):
        """
        Compte le nombre de dossiers dont la decision_projet == 'Avis défavorable'
        pour l'année concernée.
        """
        for record in self:
            if record.annee:
                # On cherche dans le modèle dossier
                # en prenant uniquement ceux dont le champ annee == record.annee
                # et la decision_projet == 'Avis favorable'
                domain = [
                    ('annee', '=', record.annee),
                    ('decision_projet', '=', 'Avis défavorable')
                ]
                count = self.env['projet'].search_count(domain)
                record.nb_dossiers_defavorables = count
            else:
                record.nb_dossiers_defavorables = 0
    @api.depends('annee')
    def _compute_nb_dossiers_complement(self):
        """
        Compte le nombre de dossiers dont la decision_projet == 'Complément'
        pour l'année concernée.
        """
        for record in self:
            if record.annee:
                # On cherche dans le modèle dossier
                # en prenant uniquement ceux dont le champ annee == record.annee
                # et la decision_projet == 'Avis favorable'
                domain = [
                    ('annee', '=', record.annee),
                    ('decision_projet', '=', 'Complément')
                ]
                count = self.env['projet'].search_count(domain)
                record.nb_dossiers_complement = count
            else:
                record.nb_dossiers_complement = 0
    @api.depends('annee')
    def _compute_nb_dossiers_reprogrammes(self):
        """
        Compte le nombre de dossiers dont la decision_projet == 'Reprogrammer'
        pour l'année concernée.
        """
        for record in self:
            if record.annee:
                # On cherche dans le modèle dossier
                # en prenant uniquement ceux dont le champ annee == record.annee
                # et la decision_projet == 'Avis favorable'
                domain = [
                    ('annee', '=', record.annee),
                    ('decision_projet', '=', 'Reprogrammer')
                ]
                count = self.env['projet'].search_count(domain)
                record.nb_dossiers_reprogrammes = count
            else:
                record.nb_dossiers_reprogrammes = 0
    # Délais moyens
    delai_moyen_reactivite_spoc = fields.Float(string="Délai moyen de réactivité SPOC", compute="_compute_stats_projet", store=True)
    delai_moyen_traitement_projet = fields.Float(string="Délai moyen de traitement projet", compute="_compute_stats_projet", store=True)
    delai_moyen_examen_crui = fields.Float(string="Délai moyen d'examen CRUI", compute="_compute_stats_projet", store=True)

    # Pourcentages
    pourcentage_dossiers_soumis_30j = fields.Float(string="% Dossiers soumis ≤ 30j", compute="_compute_stats_projet", store=True)
    pourcentage_dossiers_examines_30j = fields.Float(string="% Dossiers examinés ≤ 30j", compute="_compute_stats_projet", store=True)
    pourcentage_dossiers_approuves = fields.Float(string="% Dossiers approuvés", compute="_compute_stats_projet", store=True)
    pourcentage_investissement_realise = fields.Float(string="% Investissement réalisé", compute="_compute_stats_projet", store=True)
    pourcentage_emplois_realises = fields.Float(string="% Emplois réalisés", compute="_compute_stats_projet", store=True)

    # Totaux
    montant_investissement_total = fields.Float(string="Montant total d'investissement", compute="_compute_stats_projet", store=True)
    nombre_emploi_total = fields.Integer(string="Nombre total d'emplois", compute="_compute_stats_projet", store=True)
    @api.depends('annee')
    def _compute_stats_projet(self):
        for rec in self:
            projets = self.env['projet'].search([('annee', '=', rec.annee)])

            if not projets:
                rec.delai_moyen_reactivite_spoc = 0
                rec.delai_moyen_traitement_projet = 0
                rec.delai_moyen_examen_crui = 0
                rec.pourcentage_dossiers_soumis_30j = 0
                rec.pourcentage_dossiers_examines_30j = 0
                rec.pourcentage_dossiers_approuves = 0
                rec.pourcentage_investissement_realise = 0
                rec.pourcentage_emplois_realises = 0
                rec.montant_investissement_total = 0
                rec.nombre_emploi_total = 0
                continue

            # Agrégation par moyenne ou somme
            total_projets = len(projets)
            rec.delai_moyen_reactivite_spoc = sum(projets.mapped('delai_moyen_reactivite_spoc')) / total_projets
            rec.delai_moyen_traitement_projet = sum(projets.mapped('delai_moyen_traitement_projet')) / total_projets
            rec.delai_moyen_examen_crui = sum(projets.mapped('delai_moyen_examen_crui')) / total_projets
            rec.pourcentage_dossiers_soumis_30j = sum(projets.mapped('pourcentage_dossiers_soumis_30j')) / total_projets
            rec.pourcentage_dossiers_examines_30j = sum(projets.mapped('pourcentage_dossiers_examines_30j')) / total_projets
            rec.pourcentage_dossiers_approuves = sum(projets.mapped('pourcentage_dossiers_approuves')) / total_projets
            rec.pourcentage_investissement_realise = sum(projets.mapped('pourcentage_investissement_realise')) / total_projets
            rec.pourcentage_emplois_realises = sum(projets.mapped('pourcentage_emplois_realises')) / total_projets
            rec.montant_investissement_total = sum(projets.mapped('montant_investissement'))
            rec.nombre_emploi_total = sum(projets.mapped('nombre_emploi'))