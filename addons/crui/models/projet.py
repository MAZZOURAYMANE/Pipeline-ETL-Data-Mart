
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import PyPDF2
from io import BytesIO
import re
import base64
import pdfplumber
import logging
from odoo.exceptions import UserError
from datetime import datetime
from odoo import models, fields, api
from docx import Document
from odoo.tools.misc import xlsxwriter
from docx.shared import Inches, Pt
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)

class Projet(models.Model):
    _name = 'projet'
    _description = 'projet'

    identifiant_projet = fields.Char(string = "Identifiant du projet")
    reference = fields.Char(string="Réference Projet")
    decision_projet = fields.Char(
        string="Décision finale du projet",
        compute="_compute_decision_projet",
        store=True
    )
    dispositions_urbanistiques = fields.Text(string="Dispositions urbanistiques")
    historique_projet = fields.Text(string="Historique du projet")
    name = fields.Char(string="Intitulé")
    consistance = fields.Text(string="Consistance")
    composante = fields.Text(string="Composante")
    petitionnaire_id = fields.Many2one('res.partner', string="Pétitionnaire")
    petitionnaire = fields.Char(string="Nom & Prénom", related="petitionnaire_id.name")
    telephone = fields.Char(string="Téléphone",related=  "petitionnaire_id.phone")
    adresse = fields.Char(string="Adresse",related=  "petitionnaire_id.street")
    email = fields.Char(string="Email",related=  "petitionnaire_id.email")
    secteurs = fields.Many2many('secteur', string="Secteur", widget="many2many")
    prefecture_id = fields.Many2one('prefecture',string='Province ou Préfecture')
    commune_id = fields.Many2one('commune',string='Commune')
    raison_social = fields.Char(string="Raison Social")
    forme_juridique = fields.Selection([
        ('', ''),
        ('Société anonyme (SA)','Société anonyme (SA)'),
        ('Société à Responsabilité Limitée (SARL)','Société à Responsabilité Limitée (SARL)'),
        ('Gérance libre','Gérance libre'),
        ('Etablissement Public','Etablissement Public'),
        ('Commerçant','Commerçant'),
        ('Auto-entrepreneur','Auto-entrepreneur'),
        ('Association / Amicale','Association / Amicale'),
        ('Collectivité Territoriale','Collectivité Territoriale'),
        ('Coopérative', 'Coopérative'),
        ('Société civile immobilière (SCI)', 'Société civile immobilière (SCI)'),
        ('Succursales ou agences de commerçants', 'Succursales ou agences de commerçants'),
    ],string="Forme Juridique")
    surface = fields.Char( string="Superficie de la parcelle")
    foncier_id = fields.Many2one('foncier',
        string='Statut juridique parcelle',
    )
    fonciers = fields.Many2many('foncier', string="Foncier", widget="many2many")
    reference_fonciere = fields.Char(string="Référence fonciére")
    montant_investissement = fields.Float(string="Montant Investissement En MAD",digits=(15, 5))
    nombre_emploi = fields.Integer(string="Nombre Emplois créés")
    conseiller_id = fields.Many2one('res.users', string="SPOC", default=lambda self: self.env.user)
    montant_investissement_composante_dominante = fields.Float(string="Montant investissement de la composante dominante en MAD",digits=(15, 5))
    composante_dominante = fields.Char(string="Composante dominante")
    macro_secteurs = fields.Many2many('macrosecteur', string="Macro secteur", widget="many2many")
    nombre_emploi_composante_dominante = fields.Integer(string="Nb emplois crees de la composante dominante")
    fiche_projet = fields.Binary(string="Fiche Projet")
    fiche_projet_filename = fields.Char(string="Nom du fichier PDF")
    plan_masse = fields.Binary(string="Plan de Masse")
    plan_masse_filename = fields.Char(string="Nom Plan de Masse")
    plan_situation = fields.Binary(string="Plan de Situation")
    plan_situation_filename = fields.Char(string="Nom Plan de Situation")
    date_lancement = fields.Datetime(string='Date de lancement du projet')
    date_achevement = fields.Datetime(string='Date prévisionnelle d\'achévement des travaux')
    statut = fields.Selection([
        ('nouveau','Nouveau'),
        ('chez l\'investisseur', 'Chez l\'investisseur'),
        ('traitement spoc','Traitement spoc'),
        ('traitement crui','Traitement crui'),
        ('traitement post crui', 'Traitement post crui'),
        ('clôturé', 'clôturé'),

    ], default="nouveau", string="Statut du Projet")
    dossier_ids = fields.One2many("dossier", 'projet_id', string="Dossier")
    enquete_ids = fields.One2many("enquete", 'projet_id', string="Enquete")
    soumission_ids = fields.One2many("soumission", 'projet_id', string="Soumission")
    duree_projet = fields.Integer(string="Durée du projet", compute='_compute_duree_projet', store=True)
    nombre_dossier = fields.Integer(string="Nombre de projets", compute="_compter_nombre_dossier")
    nombre_soumission = fields.Integer(string="Nombre de soumissions", compute="_compter_nombre_soumission")
    nombre_enquete = fields.Integer(string="Nombre d'enquêtes", compute="_compter_nombre_enquete")

    annee = fields.Integer(
        string="Année",
        compute="_compute_annee",
        store=True
    )

    @api.depends('dossier_ids.date_depot')
    def _compute_annee(self):
        """ Récupère l'année de la date de dépôt la plus récente parmi les dossiers liés """
        for rec in self:
            # Filtrer les dossiers avec une date de dépôt valide
            dates = rec.dossier_ids.filtered(lambda d: d.date_depot).mapped('date_depot')
            if dates:
                rec.annee = min(dates).year  # Prendre l'année de la date la plus récente
            else:
                rec.annee = False

    @api.depends('date_lancement', 'date_achevement')
    def _compute_duree_projet(self):
        for rec in self:
            if rec.date_lancement and rec.date_achevement:
                rec.duree_projet = (rec.date_achevement - rec.date_lancement).days
            else:
                rec.duree_projet = 0

    def action_cloturer(self):
        self.statut ="clôturé"

    def action_check_and_fix_soumission_dates(self):
        self.ensure_one()
        return self.env['soumission'].action_check_and_fix_dates()

    # Control 
    @api.onchange('reference_fonciere')
    def _onchange_reference_fonciere(self):
        """ Vérifie si la référence foncière existe déjà dans la base et affiche un avertissement """
        if self.reference_fonciere:
            existing_project = self.env['projet'].search([
                ('reference_fonciere', '=', self.reference_fonciere),
                ('id', '!=', self.id)  # Exclure l'enregistrement en cours
            ], limit=1)

            if existing_project:
                return {
                    'warning': {
                        'title': "Référence foncière existante",
                        'message': f"La référence foncière '{self.reference_fonciere}' existe déjà pour un autre projet ({existing_project.name}).",
                    }
                }
    #nombre soumission, enquetes et dossiers par projet
    @api.depends("dossier_ids")
    def _compter_nombre_dossier(self):  
        for rec in self:
            rec.nombre_dossier = len(rec.dossier_ids) 
    @api.depends("soumission_ids")
    def _compter_nombre_soumission(self):  
        for rec in self:
            rec.nombre_soumission = len(rec.soumission_ids) 
    @api.depends("enquete_ids")
    def _compter_nombre_enquete(self):  
        for rec in self:
            rec.nombre_enquete = len(rec.enquete_ids) 
    
    #KPI 
    # INDICATEUR 0
    delai_moyen_reactivite_spoc = fields.Float(
        string="Délai moyen de réactivité SPOC (jours)",
        compute='_compute_delai_moyen_reactivite_spoc',
        store=True
    )
    
    @api.depends('soumission_ids.delai_reactivite_spoc')
    def _compute_delai_moyen_reactivite_spoc(self):
        for rec in self:
            soumissions = rec.soumission_ids.filtered(lambda s: s.delai_reactivite_spoc is not False and s.delai_reactivite_spoc >= 0)
            if soumissions:
                total = sum(soumissions.mapped('delai_reactivite_spoc'))
                rec.delai_moyen_reactivite_spoc = total / len(soumissions)
            else:
                rec.delai_moyen_reactivite_spoc = 0
    # INDICATEUR 1
    delai_moyen_traitement_projet = fields.Float(
        string=" INDICATEUR 1: Le délai moyen de traitement d’un dossier d’investissement complet déposé auprès du CRI et de sa soumission à la CRUI.",
        compute="_compute_delai_moyen_traitement_projet",
        store=True)

    
    @api.depends('dossier_ids.delai_moyen_traitement')
    def _compute_delai_moyen_traitement_projet(self):
        for rec in self:
            dossiers = rec.dossier_ids.filtered(lambda d: d.delai_moyen_traitement is not None and d.delai_moyen_traitement > 0)
            if dossiers:
                total = sum(dossiers.mapped('delai_moyen_traitement'))
                rec.delai_moyen_traitement_projet = total / len(dossiers)
            else:
                rec.delai_moyen_traitement_projet = 0
    # INDICATEUR 2
    pourcentage_dossiers_soumis_30j = fields.Float(
        string="INDICATEUR 2: Le pourcentage de dossiers d’investissement traités soumis par le CRI à la CRUI dans un délai maximum de 30 jours, à compter de la date de leur dépôt complet auprès dudit Centre",
        compute="_compute_pourcentage_dossiers_soumis_30j",
        store=True
    )
    
    @api.depends('dossier_ids.date_depot', 'dossier_ids.date_diffusion', 'dossier_ids.soumis_30j')
    def _compute_pourcentage_dossiers_soumis_30j(self):
        for rec in self:
            # On considère seulement les dossiers qui ont été déposés et diffusés (i.e., traités)
            dossiers_traite = rec.dossier_ids.filtered(lambda d: d.date_depot and d.date_diffusion)
            dossiers_soumis_30j = dossiers_traite.filtered(lambda d: d.soumis_30j)

            if dossiers_traite:
                rec.pourcentage_dossiers_soumis_30j = (len(dossiers_soumis_30j) / len(dossiers_traite)) * 100
            else:
                rec.pourcentage_dossiers_soumis_30j = 0

    #INDICATEUR 3
    delai_moyen_examen_crui = fields.Float(
        string="INDICATEUR 3: Le délai moyen d’examen et de prise de décision concernant les dossiers d’investissement par la CRUI",
        compute="_compute_delai_moyen_examen_crui",
        store=True
    )
    @api.depends('dossier_ids.delai_examen_crui')
    def _compute_delai_moyen_examen_crui(self):
        """ Calcule la moyenne des délais d'examen par la CRUI pour tous les dossiers d'un projet """
        for rec in self:
            dossiers_concernes = rec.dossier_ids.filtered(lambda d: d.date_diffusion and d.date_passage)

            if dossiers_concernes:
                rec.delai_moyen_examen_crui = sum(dossiers_concernes.mapped('delai_examen_crui')) / len(dossiers_concernes)
            else:
                rec.delai_moyen_examen_crui = 0
    #INDICATEUR 4
    pourcentage_dossiers_examines_30j = fields.Float(
        string="Dossiers examinés ≤ 30 jours (%)",
        compute="_compute_pourcentage_dossiers_examines_30j",
        store=True
        )
    @api.depends('dossier_ids.examine_30j', 'dossier_ids.decision_crui')
    def _compute_pourcentage_dossiers_examines_30j(self):
        """ Calcule le pourcentage des dossiers examinés en ≤ 30 jours après leur diffusion,
            uniquement pour les dossiers ayant une décision CRUI finale """
        decisions_valides = ['Avis favorable', 'Avis favorable sous réserve', 'Avis défavorable']
        
        for rec in self:
            dossiers_concernes = rec.dossier_ids.filtered(
                lambda d: d.date_diffusion and d.date_passage and d.decision_crui in decisions_valides
            )
            dossiers_examines_30j = dossiers_concernes.filtered(lambda d: d.examine_30j)

            if dossiers_concernes:
                rec.pourcentage_dossiers_examines_30j = (len(dossiers_examines_30j) / len(dossiers_concernes)) * 100
            else:
                rec.pourcentage_dossiers_examines_30j = 0


    #Indicateur 5
    pourcentage_dossiers_approuves = fields.Float(
        string="Dossiers approuvés (%)",
        compute="_compute_pourcentage_dossiers_approuves",
        store=True
    )
    @api.depends('dossier_ids.approuve_crui')
    def _compute_pourcentage_dossiers_approuves(self):
        """ Calcule le pourcentage de dossiers approuvés par la CRUI """
        for rec in self:
            dossiers_totaux = rec.dossier_ids.filtered(lambda d: d.decision_crui)
            dossiers_approuves = dossiers_totaux.filtered(lambda d: d.approuve_crui)

            if dossiers_totaux:
                rec.pourcentage_dossiers_approuves = (len(dossiers_approuves) / len(dossiers_totaux)) * 100
            else:
                rec.pourcentage_dossiers_approuves = 0
    projet_approuve = fields.Boolean(
        string="Projet approuvé (100% dossiers favorables)",
        compute="_compute_projet_approuve",
        store=True
        )      
    @api.depends('dossier_ids.decision_crui')
    def _compute_projet_approuve(self):
        for rec in self:
            dossiers = rec.dossier_ids
            if dossiers:
                rec.projet_approuve = all(d.decision_crui == 'Avis favorable' for d in dossiers)
            else:
                rec.projet_approuve = False

    #Indicateur 6   NON APPLICABLE LE MONTANT d'INVESTISSMENT TOTAL SERA CALCULE DANS GLOBAL API
    #Indicateur 7   NON APPLICABLE LE NOMBRE D'EMPLOI TOTAL SERA CALCULE DANS GLOBAL API
    #Indicateur 8
    # Champ calculé : pourcentage réalisé
    pourcentage_investissement_realise = fields.Float(
        string="INDICATEUR 8 : Pourcentage investissement réalisé (%)",
        compute="_compute_pourcentage_investissement_realise",
        store=True
    )

    @api.depends('montant_investissement', 'enquete_ids.montant_investissement_reel', 'enquete_ids.date_suivi_effectue')
    def _compute_pourcentage_investissement_realise(self):
        for rec in self:
            montant_prevu = rec.montant_investissement or 0
            montant_reel = 0

            # Récupérer la dernière enquête selon la date de suivi
            enquetes = rec.enquete_ids.filtered(lambda e: e.montant_investissement_reel and e.date_suivi_effectue)
            if enquetes:
                derniere_enquete = max(enquetes, key=lambda e: e.date_suivi_effectue)
                montant_reel = derniere_enquete.montant_investissement_reel

            # Calcul du pourcentage
            if montant_prevu > 0:
                rec.pourcentage_investissement_realise = (montant_reel / montant_prevu) * 100
            else:
                rec.pourcentage_investissement_realise = 0
    #Indicateur 9
    pourcentage_emplois_realises = fields.Float(
        string="INDICATEUR : Pourcentage d’emplois réalisés (%)",
        compute="_compute_pourcentage_emplois_realises",
        store=True
    )

    @api.depends('nombre_emploi', 'enquete_ids.nombre_emplois_reel', 'enquete_ids.date_suivi_effectue')
    def _compute_pourcentage_emplois_realises(self):
        for rec in self:
            emploi_prevu = rec.nombre_emploi or 0
            emploi_reel = 0

            # Récupérer la dernière enquête (par date de suivi)
            enquetes = rec.enquete_ids.filtered(lambda e: e.nombre_emplois_reel and e.date_suivi_effectue)
            if enquetes:
                derniere_enquete = max(enquetes, key=lambda e: e.date_suivi_effectue)
                emploi_reel = derniere_enquete.nombre_emplois_reel

            # Calcul du pourcentage
            if emploi_prevu > 0:
                rec.pourcentage_emplois_realises = (emploi_reel / emploi_prevu) * 100
            else:
                rec.pourcentage_emplois_realises = 0


    delai_moyen_dossiers = fields.Float(
            string="Délai moyen des dossiers (jours ouvrés)",
            compute='_compute_delai_moyen_dossiers',
            store=True
        )
    @api.depends('dossier_ids.delai_moyen_traitement')
    def _compute_delai_moyen_dossiers(self):
        for rec in self:
            dossiers = rec.dossier_ids.filtered(lambda d: d.date_diffusion)  # Ne prendre que les dossiers diffusés
            if dossiers:
                rec.delai_moyen_dossiers = sum(dossiers.mapped('delai_moyen_traitement')) / len(dossiers)
            else:
                rec.delai_moyen_dossiers = 0
        

   #indicateur 10  Délai délivrance acte
   # Délai moyen de délivrance des actes pour un projet
    delai_moyen_delivrance_acte = fields.Float(
        string="Délai moyen de délivrance des actes (jours ouvrés)",
        compute="_compute_delai_moyen_delivrance_acte",
        store=True
    )

    @api.depends('dossier_ids.delai_delivrance_act')
    def _compute_delai_moyen_delivrance_acte(self):
        for rec in self:
            dossiers = rec.dossier_ids.filtered(lambda d: d.delai_delivrance_act > 0)
            if dossiers:
                rec.delai_moyen_delivrance_acte = sum(dossiers.mapped('delai_delivrance_act')) / len(dossiers)
            else:
                rec.delai_moyen_delivrance_acte = 0



    #Extraction

    def action_extract_data_from_pdf(self):
        """ Extrait les données du PDF et met à jour les champs du projet """
        for record in self:
            if not record.fiche_projet:
                continue

            # Convertir le fichier binaire en objet PDF
            pdf_data = BytesIO(base64.b64decode(record.fiche_projet))
            text = self.extract_text_from_pdf(pdf_data)
            date_lancement, date_achevement = self.extract_last_dates(text)
            # Extraction des données
            record.name = self.extract_project_name(text)
            record.montant_investissement = self.extract_montant_investissement(text)
            record.nombre_emploi = self.extract_nombre_emplois(text)
            record.reference_fonciere = self.extract_reference_fonciere(text)
            record.date_lancement = date_lancement
            record.date_achevement = date_achevement
            record.petitionnaire_id = self.extract_petitionnaire(text)
            record.reference = self.extract_reference_dossier(text)
            record.consistance = self.extract_description_projet(text)
            record.composante = self.extract_composante(text)
            record.secteurs = self.extract_secteurs(text)
            record.commune_id = self.extract_commune(text)
            record.prefecture_id = self.extract_prefecture(text)
            record.surface = self.extract_surface(text) 
            record.fonciers = self.extract_fonciers(text)

    def extract_montant_investissement(self, text):
        """ Extrait le premier chiffre après 'Fonds' """
        match = re.search(r"Fonds\s+([\d\s,.]+)", text, re.DOTALL)
        
        if match:
            result = match.group(1).strip()

            # Prendre uniquement le premier nombre dans la chaîne extraite
            montant_match = re.search(r"(\d+)", result)
            if montant_match:
                try:
                    return float(montant_match.group(1))  # Convertir en float
                except ValueError:
                    return 0.0

        return 0.0  # Aucun montant trouvé
    def extract_text_after_travaux(self, text):
        """ Extrait tout le texte après le mot 'travaux' """
        match = re.search(r"travaux\s*(.*)", text, re.DOTALL)
        if match:
            return match.group(1).strip()  # Retourne le texte après "travaux"
        return "Texte introuvable"
    def extract_text_from_pdf(self, pdf_data):
        """ Extrait tout le texte du PDF avec pdfplumber """
        try:
            text = ""
            with pdfplumber.open(pdf_data) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise UserError(f"Erreur lors de l'extraction du texte du PDF : {str(e)}")
    def extract_fonciers(self, text):
        """ Extrait les types de foncier entre 'Type' et 'Référence Foncière' et les associe en Many2many """
        matches = re.findall(r"Type\s*(.*?)\s*Référence Foncière", text, re.DOTALL)
        foncier_ids = []

        for match in matches:
            result = match.strip()

            # Nettoyer les espaces et retours à la ligne
            result = re.sub(r"\n\s*", " ", result)

            # Vérifier si le foncier existe déjà dans la base de données
            foncier = self.env['foncier'].search([('name', '=', result)], limit=1)

            if not foncier:
                foncier = self.env['foncier'].create({'name': result})  # Création du foncier s'il n'existe pas

            foncier_ids.append(foncier.id)

        return [(6, 0, foncier_ids)]  # Format Many2many pour Odoo
    def extract_surface(self, text):
        """ Extrait la Superficie totale entre 'Superficie totale' et 'Parcelle couverte un document d’urbanisme' """
        match = re.search(r"Superficie totale\s*(.*?)\s*Parcelle couverte un document d’urbanisme", text, re.DOTALL)
        if match:
            result = match.group(1).strip()

            # Nettoyer les espaces et les éventuels retours à la ligne
            result = re.sub(r"\n\s*", " ", result)

            return result

        return "Superficie introuvable"
    def extract_prefecture(self, text):
        """ Extrait la préfecture entre 'Préfecture/Province' et 'Superficie totale' et l'ajoute en Many2one """
        match = re.search(r"Préfecture/Province\s*(.*?)\s*Superficie totale", text, re.DOTALL)
        if match:
            result = match.group(1).strip()

            # Nettoyer les retours à la ligne
            result = re.sub(r"\n\s*", " ", result)

            # Vérifier si la préfecture existe déjà dans la base de données
            prefecture = self.env['prefecture'].search([('name', '=', result)], limit=1)

            if not prefecture:
                prefecture = self.env['prefecture'].create({'name': result})  # Création de la préfecture si elle n'existe pas

            return prefecture.id  # Retourne l'ID de la préfecture

        return False  # Aucun résultat trouvé
    def extract_commune(self, text):
        """ Extrait la commune entre 'Commune' et 'Préfecture/Province' et l'ajoute en Many2one """
        match = re.search(r"Commune\s*(.*?)\s*Préfecture/Province", text, re.DOTALL)
        if match:
            result = match.group(1).strip()

            # Nettoyer les retours à la ligne
            result = re.sub(r"\n\s*", " ", result)

            # Vérifier si la commune existe déjà dans la base de données
            commune = self.env['commune'].search([('name', '=', result)], limit=1)

            if not commune:
                commune = self.env['commune'].create({'name': result})  # Création de la commune si elle n'existe pas

            return commune.id  # Retourne l'ID de la commune

        return False  # Aucun résultat trouvé
    
    def extract_secteurs(self, text):
        """ Extrait le secteur d’activité entre 'd’activité de la composante' et 'dominante)' et l'ajoute en Many2many """
        match = re.search(r"d’activité de la composante\s*(.*?)\s*dominante\)", text, re.DOTALL)
        if match:
            result = match.group(1).strip()

            # Nettoyer les espaces et les éventuels retours à la ligne
            result = re.sub(r"\n\s*", " ", result)

            # Vérifier si le secteur existe déjà dans la base de données
            secteur = self.env['secteur'].search([('name', '=', result)], limit=1)

            if not secteur:
                secteur = self.env['secteur'].create({'name': result})  # Création du secteur s'il n'existe pas

            return [(6, 0, [secteur.id])]  # Format Many2many pour Odoo

        return [(6, 0, [])]  # Aucun secteur trouvé
    def extract_description_projet(self, text):
        """ Extrait la description du projet entre la référence du dossier (C1 à C11) et 'Composantes' """
        match = re.search(r"Référence du dossier\s*\S*\/C\d{1,2}\s*(.*?)\s*Composantes", text, re.DOTALL)
        if match:
            result = match.group(1).strip()

            # Supprimer "Description du projet" s'il est présent dans le texte
            result = re.sub(r"\bDescription du projet\b", "", result, flags=re.IGNORECASE)

            # Supprimer les retours à la ligne inutiles
            result = re.sub(r"\n\s*", " ", result)

            return result

        return "Description introuvable"
    def extract_composante(self, text):
        """ Extrait les composantes du projet entre 'Composantes' et 'Secteur d’activité' """
        match = re.search(r"Composantes\s*(.*?)\s*Secteur d’activité", text, re.DOTALL)
        if match:
            result = match.group(1).strip()

            # Supprimer les retours à la ligne inutiles
            result = re.sub(r"\n\s*", " ", result)

            return result

        return "Composante introuvable"
    def extract_project_name(self, text):
        """ Extrait le nom du projet après 'Fiche du projet :' en tenant compte des lignes suivantes """
        match = re.search(r"Fiche du projet\s*:\s*(.+)", text, re.DOTALL)
        if match:
            result = match.group(1).strip()
            
            # Supprimer d'éventuelles coupures de ligne trop longues
            result = re.sub(r"\n\s*", " ", result)  # Remplace les retours à la ligne par un espace

            # Arrêter l'extraction si une ligne commence par un mot-clé indiquant une nouvelle section
            stop_words = ["Typologie du projet", "Secteur d’activité", "Localisation du projet", "Date de lancement","X"]
            for stop_word in stop_words:
                result = re.split(rf"\b{stop_word}\b", result)[0].strip()
            
            return result
        
        return "Nom introuvable"
    def extract_petitionnaire(self, text):
        """ Extrait le pétitionnaire après 'Investisseur' ou immédiatement avant """
        match = re.search(r"(PM|PP/AE)\s*(.+?)\s*Investisseur", text, re.DOTALL)
        if match:
            result = match.group(2).strip()  # Récupérer uniquement le nom

            # Vérifier si un partenaire existe déjà avec ce nom
            partner = self.env['res.partner'].search([('name', '=', result)], limit=1)

            if not partner:
                # Créer un nouveau partenaire si introuvable
                partner = self.env['res.partner'].create({'name': result})

            return partner.id  # Retourne l'ID du partenaire

        return False
    def extract_reference_dossier(self, text):
        """ Extrait la Référence du dossier après 'Référence du dossier' """
        match = re.search(r"Référence du dossier\s*([\w/\-]+)", text)
        if match:
            return match.group(1).strip()
        return "Référence introuvable"
    

    def extract_nombre_emplois(self, text):
        """ Extrait le nombre d'emplois créés """
        match = re.search(r"Nombre d'emplois\s+(\d+)", text)
        if match:
            return int(match.group(1))
        return None

    def extract_reference_fonciere(self, text):
        """ Extrait la référence foncière """
        match = re.search(r"Référence Foncière\s*(\S+)", text)
        if match:
            return match.group(1).strip()
        return None

    def extract_date_lancement(self, text):
        """ Extrait et convertit la date de lancement du projet au format Odoo (Datetime) """
        match = re.search(r"Date de lancement\s*du projet\s*(\d{2}/\d{2}/\d{4})", text)
        if match:
            date_str = match.group(1).strip()
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")  # Convertir en datetime (sans heure)
            return fields.Datetime.to_string(date_obj)  # Conversion en format Odoo (YYYY-MM-DD HH:MM:SS)
        return None

    def extract_date_achevement(self, text):
        """ Extrait et convertit la date prévisionnelle d’achèvement des travaux au format Odoo (Datetime) """
        match = re.search(r"Date prévisionnelle\s*d’achèvement\s*des\s*travaux\s*(\d{2}/\d{2}/\d{4})", text)
        if match:
            date_str = match.group(1).strip()
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")  # Convertir en datetime (sans heure)
            return fields.Datetime.to_string(date_obj)  # Conversion en format Odoo (YYYY-MM-DD HH:MM:SS)
        return None
    def extract_last_dates(self, text):
        """ Extrait les deux dernières dates au format DD/MM/YYYY depuis la fin du fichier """
        matches = re.findall(r"\b(\d{2}/\d{2}/\d{4})\b", text)  # Trouver toutes les dates dans le document
        
        if len(matches) >= 3:
            date_achevement_str = matches[-2]  # Avant-dernière date trouvée (date d’achèvement)
            date_lancement_str = matches[-3]  # Avant-avant-dernière date trouvée (date de lancement)
        elif len(matches) == 2:
            date_achevement_str = matches[-2]  # Prendre l’avant-dernière date
            date_lancement_str = None  # Pas assez de dates pour la date de lancement
        else:
            return None, None  # Pas assez de dates trouvées

        try:
            date_achevement = datetime.strptime(date_achevement_str, "%d/%m/%Y")  # Conversion en datetime
            date_achevement = fields.Datetime.to_string(date_achevement)  # Format Odoo (YYYY-MM-DD HH:MM:SS)
        except ValueError:
            date_achevement = None

        try:
            date_lancement = datetime.strptime(date_lancement_str, "%d/%m/%Y") if date_lancement_str else None
            date_lancement = fields.Datetime.to_string(date_lancement) if date_lancement else None
        except ValueError:
            date_lancement = None

        return date_lancement, date_achevement
    @api.depends('dossier_ids.decision_dossier')
    def _compute_decision_projet(self):
        priority_order = [
            'Avis défavorable',
            'Reprogrammer',
            'Complément',
            'Avis favorable sous réserve',
            'Avis favorable'
        ]
        for record in self:
            decisions = record.dossier_ids.mapped('decision_dossier')
            # On filtre les décisions non nulles
            decisions = [d for d in decisions if d]

            for decision in priority_order:
                if decision in decisions:
                    record.decision_projet = decision
                    break
            else:
                record.decision_projet = False  # Aucun dossier avec une décision renseignée
    docx_file = fields.Binary("Fichier généré", readonly=True)
    docx_filename = fields.Char("Nom du fichier généré", readonly=True)
    docx_mimetype = fields.Char(default='application/vnd.openxmlformats-officedocument.wordprocessingml.document')


    def action_generate_docx_summary(self):

        for rec in self:
            # Construire l'historique du projet
            dossier_actuel = self.env['dossier'].search([
                ('projet_id', '=', rec.id),
                ('statut_dossier', '=', 'crui')
            ], order='date_passage desc', limit=1)

            _logger.info(f"PV Projet {rec.id}: Dossier actuel trouvé: {dossier_actuel.id if dossier_actuel else 'Aucun'}, Date: {dossier_actuel.date_passage if dossier_actuel else 'Aucune'}")

            historique_projet = ""
            if dossier_actuel and dossier_actuel.date_passage:
                # Rechercher tous les dossiers CRUI antérieurs
                dossiers_anterieurs = self.env['dossier'].search([
                    ('projet_id', '=', rec.id),
                    ('statut_dossier', '=', 'crui'),
                    ('date_passage', '<', dossier_actuel.date_passage),
                    ('id', '!=', dossier_actuel.id)
                ], order='date_passage desc')

                _logger.info(f"PV Projet {rec.id}: Nombre de dossiers antérieurs trouvés: {len(dossiers_anterieurs)}")

                if dossiers_anterieurs:
                    historique_lignes = []
                    for dossier_ant in dossiers_anterieurs:
                        date_passage_ant = dossier_ant.date_passage.strftime('%d/%m/%Y') if dossier_ant.date_passage else "Date non renseignée"
                        decision_crui = dossier_ant.decision_crui or "Décision non renseignée"
                        historique_lignes.append(f"• Passage CRUI du {date_passage_ant} : {decision_crui}")
                        _logger.info(f"PV Projet {rec.id}: Ajout historique - Date: {date_passage_ant}, Décision: {decision_crui}")

                    historique_projet = "\n".join(historique_lignes)
                else:
                    _logger.info(f"PV Projet {rec.id}: Aucun dossier antérieur, projet non programmé précédemment")
            else:
                _logger.warning(f"PV Projet {rec.id}: Aucun dossier CRUI actuel trouvé ou sans date de passage")

            doc = Document()
            logo_path = get_module_resource('crui', 'static/img', 'logo.png')
            # Insertion du logo centré
            if logo_path:
                header = doc.sections[0].header
                paragraph = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
                paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                run = paragraph.add_run()
                run.add_picture(logo_path, width=Inches(2))  # ajuste la taille si nécessaire
            # ENCADRÉ DE TITRE
            heading = doc.add_paragraph()
            heading.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER 
            run = heading.add_run(
                f"PV de la réunion de la CRUI du {rec.dossier_ids[:1].date_passage.strftime('%d/%m/%Y') if rec.dossier_ids and rec.dossier_ids[:1].date_passage else '____'} au siège du CRI Fès Meknès\n"
                f"Projet : {rec.name or ''}\n"
                f"Référence du dossier : {rec.reference or ''}  URL : {rec.identifiant_projet or ''}"
            )
            run.bold = True
            run.font.size = Pt(12)

            p = heading._element
            pPr = p.get_or_add_pPr()
            borders = OxmlElement('w:pBdr')
            for border_name in ('top', 'left', 'bottom', 'right'):
                border_el = OxmlElement(f'w:{border_name}')
                border_el.set(qn('w:val'), 'single')
                border_el.set(qn('w:sz'), '6')
                border_el.set(qn('w:space'), '1')
                border_el.set(qn('w:color'), 'auto')
                borders.append(border_el)
            pPr.insert(0, borders)
            # TABLEAU D’INFOS
            table = doc.add_table(rows=0, cols=2)
            table.style = 'Table Grid'

            def add_row(label, value, bold_label=False, background=False):
                row = table.add_row().cells
                row[0].text = label
                row[1].text = value or ""
                for cell in row:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(11)
                if bold_label:
                    for run in row[0].paragraphs[0].runs:
                        run.bold = True
                if background:
                    shading = OxmlElement('w:shd')
                    shading.set(qn('w:fill'), 'D9D9D9')
                    row[0]._tc.get_or_add_tcPr().append(shading)

            add_row("Investisseur", rec.petitionnaire or "", bold_label=True, background=True)
            add_row("Description du projet", rec.consistance or "", bold_label=True, background=True)
            add_row("Localisation", rec.prefecture_id.name if rec.prefecture_id else "", bold_label=True, background=True)
            add_row("Superficie", rec.surface or "", bold_label=True, background=True)
            add_row("Dispositions urbanistiques", rec.dispositions_urbanistiques or "", bold_label=True, background=True)
            add_row("Statut juridique du terrain", rec.foncier_id.name if rec.foncier_id else "", bold_label=True, background=True)
            add_row("Références foncières du terrain", rec.reference_fonciere or "", bold_label=True, background=True)

            row = table.add_row().cells
            row[0].text = "Montant d’investissement MDHs"
            row[1].text = f"{rec.montant_investissement:.2f}"
            row2 = table.add_row().cells
            row2[0].text = "Nombre d’emplois"
            row2[1].text = str(rec.nombre_emploi or "")
            for r in (row + row2):
                for paragraph in r.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(11)
            for run in row[0].paragraphs[0].runs + row2[0].paragraphs[0].runs:
                run.bold = True

            add_row("Historique du projet", historique_projet, bold_label=True, background=True)
            actes = ", ".join(rec.dossier_ids.mapped('actes_ids.name')) if rec.dossier_ids else ""
            add_row("Actes demandés", actes, bold_label=True, background=True)

            # TITRE AVIS
            p_avis = doc.add_paragraph()
            run = p_avis.add_run("Avis de la commission")
            run.bold = True
            run.font.size = Pt(12)
            p_avis.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

            # CONTENU AVIS (dans tableau)
            table_avis = doc.add_table(rows=1, cols=1)
            table_avis.style = 'Table Grid'
            avis_text = rec.dossier_ids[:1].decision_crui or ""
            argumentaire = rec.dossier_ids[:1].argument_crui or ""
            cell = table_avis.cell(0, 0)
            cell.text = f"{avis_text}\n{argumentaire}"
            for run in cell.paragraphs[0].runs:
                run.bold = True
                run.font.size = Pt(11)

            # SIGNATURE
            table_sign = doc.add_table(rows=1, cols=1)
            table_sign.style = 'Table Grid'
            cell = table_sign.cell(0, 0)
            p_sign = cell.paragraphs[0]
            run = p_sign.add_run("Monsieur le Directeur Général du CRI Fès Meknès\n\n\n")
            run.bold = True
            run.font.size = Pt(11)
            p_sign.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

            # Construire la liste complète des signataires
            signataires = []

            # Signataires obligatoires dans l'ordre
            signataires.append("Conseil de la Région Fès-Meknès")
            signataires.append("Wilaya de la Région Fès-Meknès")

            # Ajouter la Préfecture/Province concernée
            if rec.prefecture_id:
                signataires.append(f"Préfecture / Province de : {rec.prefecture_id.name}")

            # Ajouter la Commune concernée
            if rec.commune_id:
                signataires.append(f"Commune de:  {rec.commune_id.name}")

            # Ajouter les autres membres de la commission
            membres = rec.dossier_ids[:1].commission_id.mapped('membre_ids')
            if membres:
                for membre in membres:
                    if membre.name:
                        signataires.append(membre.name)

            # Ajouter Maroc Telecom et SRM-FM (signataires obligatoires finaux)
            signataires.append("Maroc Telecom")
            signataires.append("SRM-FM")

            # Créer le tableau des signataires
            if signataires:
                table_commission = doc.add_table(rows=0, cols=3)
                table_commission.alignment = WD_TABLE_ALIGNMENT.CENTER
                table_commission.style = 'Table Grid'

                row = None
                for i, signataire in enumerate(signataires):
                    if i % 3 == 0:
                        row = table_commission.add_row().cells
                    cell = row[i % 3]
                    para = cell.paragraphs[0]
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = para.add_run(signataire)
                    run.font.size = Pt(11)
                    run.add_break()  # 1ère ligne vide
                    run.add_break()  # 2ème ligne vide
                    run.add_break()  # 3ème ligne vide

                # Ligne Q : / [nombre_total]  C :
                # Nombre total = nombre de signataires + 1
                nombre_total = len(signataires) + 1
                doc.add_paragraph()
                last_row = table_commission.add_row().cells
                last_row[0].merge(last_row[2])
                para = last_row[0].paragraphs[0]
                para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = para.add_run(f"Q :      / {nombre_total}\nC :")
                run.font.size = Pt(11)
                run.bold = True

            doc.add_paragraph()  # Espace
            p_remarques = doc.add_paragraph()
            date_crui = rec.dossier_ids[:1].date_passage.strftime('%d/%m/%Y') if rec.dossier_ids and rec.dossier_ids[:1].date_passage else "____"
            run = p_remarques.add_run(f"Remarques de la CRUI du {date_crui}")
            run.bold = True
            run.font.size = Pt(12)
            p_remarques.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            remarques_text = rec.dossier_ids[:1].remarque_crui or "Aucune remarque renseignée."
            p_remarques_texte = doc.add_paragraph(remarques_text)
            p_remarques_texte.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

            for run in p_remarques_texte.runs:
                run.font.size = Pt(11)
            # ENREGISTRER
            buffer = BytesIO()
            doc.save(buffer)
            file_data = base64.b64encode(buffer.getvalue())
            filename = f"PV_CRUI_{rec.identifiant_projet or 'projet'}.docx"

            rec.write({
                'docx_file': file_data,
                'docx_filename': filename,
            })

            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/projet/{rec.id}/docx_file?download=true&filename={filename}',
                'target': 'self',
            }
