from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
from io import BytesIO
from odoo.tools.misc import xlsxwriter
import logging

_logger = logging.getLogger(__name__)

class SituationProjetWizard(models.TransientModel):
    _name = 'situation.projet.wizard'
    _description = 'Wizard pour générer la Situation des Projets XLSX'

    date_passage = fields.Date(
        string="Date de passage CRUI", 
        required=True, 
        default=fields.Date.context_today,
        help="Sélectionnez la date de passage pour générer le rapport"
    )
    
    file_data = fields.Binary(
        string="Fichier généré",
        readonly=True
    )

    file_name = fields.Char(
        string="Nom du fichier",
        readonly=True
    )

    @api.onchange('date_passage')
    def _onchange_date_passage(self):
        """Affiche un avertissement dynamique si un week-end est sélectionné."""
        if self.date_passage and self.date_passage.weekday() >= 5:  # 5 = Samedi, 6 = Dimanche
            return {
                'warning': {
                    'title': 'Jour non ouvré',
                    'message': 'Vous avez sélectionné un week-end (Samedi ou Dimanche). Veuillez choisir un jour de la semaine.'
                }
            }

    @api.constrains('date_passage')
    def _check_date_passage(self):
        """Bloque complètement la génération si la date reste un week-end."""
        for record in self:
            if record.date_passage and record.date_passage.weekday() >= 5:
                raise ValidationError("La date de passage CRUI ne peut pas être un week-end (Samedi ou Dimanche).")

    def action_generate_report(self):
        """Génère le rapport Excel basé sur la date de passage sélectionnée"""
        self.ensure_one()
        
        if not self.date_passage:
            raise UserError("Veuillez sélectionner une date de passage.")
            
        start_date = fields.Datetime.to_string(fields.Datetime.from_string(str(self.date_passage) + ' 00:00:00'))
        end_date = fields.Datetime.to_string(fields.Datetime.from_string(str(self.date_passage) + ' 23:59:59'))
        
        # Utilisation de sudo() pour contourner les règles de sécurité et extraire tous les dossiers
        dossiers = self.env['dossier'].sudo().search([
            ('date_passage', '>=', start_date),
            ('date_passage', '<=', end_date)
        ])
        
        if not dossiers:
            raise UserError(f"Aucun dossier trouvé pour la date de passage du {self.date_passage.strftime('%d/%m/%Y')}.")
            
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('global')

        # Formats
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#D3D3D3', 'border': 1, 
            'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        })
        cell_format = workbook.add_format({'border': 1, 'valign': 'vcenter'})
        date_format = workbook.add_format({'border': 1, 'num_format': 'dd/mm/yyyy', 'valign': 'vcenter'})

        headers = [
            "N°", "ID dossier", "SPOC", "Préfecture ou Province", "Actes", "Références", 
            "Intitulé du Projet", "Secteur", "Commune", "Pétitionnaire", "Mt Invest (Mdh)", 
            "Nombre d'emplois à créer", "Date CRUI", "Décisions CRUI", "Situation de l'action", 
            "Date lancement action", "Date", "Nombre de jours", "Délai", 
            "Situation globale", "Date levée de reserve", "Date délivrance Acte", 
            "Délai délivrance Acte", "Délai réglementaire", "Retard en Nbr de jours pour la délivrance", 
            "Dans les delais OUI/NON", "Observation"
        ]

        for col_num, header in enumerate(headers):
            sheet.write(0, col_num, header, header_format)
            sheet.set_column(col_num, col_num, 16)

        row = 1
        for i, dossier in enumerate(dossiers, 1):
            projet = dossier.projet_id
            actions = dossier.action_ids if dossier.action_ids else [None]
            
            for action in actions:
                sheet.write(row, 0, i, cell_format)
                sheet.write(row, 1, str(dossier.dossier_id) if dossier.dossier_id else (projet.identifiant_projet if projet else ''), cell_format)
                sheet.write(row, 2, projet.conseiller_id.name if projet and projet.conseiller_id else '', cell_format)
                sheet.write(row, 3, projet.prefecture_id.name if projet and projet.prefecture_id else '', cell_format)
                
                actes = ", ".join(dossier.actes_ids.mapped('name'))
                sheet.write(row, 4, actes, cell_format)
                
                sheet.write(row, 5, dossier.reference or '', cell_format)
                sheet.write(row, 6, projet.name if projet else dossier.name or '', cell_format)
                
                secteurs = ", ".join(projet.secteurs.mapped('name')) if projet else ""
                sheet.write(row, 7, secteurs, cell_format)
                
                sheet.write(row, 8, projet.commune_id.name if projet and projet.commune_id else '', cell_format)
                sheet.write(row, 9, projet.petitionnaire if projet else '', cell_format)
                
                mt_invest = (projet.montant_investissement / 1000000.0) if projet and projet.montant_investissement else 0.0
                sheet.write(row, 10, mt_invest, cell_format)
                sheet.write(row, 11, projet.nombre_emploi if projet else 0, cell_format)
                
                sheet.write(row, 12, dossier.date_passage.strftime('%d/%m/%Y') if dossier.date_passage else '', date_format if dossier.date_passage else cell_format)
                
                decision = dict(dossier._fields['decision_crui'].selection).get(dossier.decision_crui, dossier.decision_crui) if dossier.decision_crui else ''
                sheet.write(row, 13, decision, cell_format)
                
                if action:
                    sit_action = dict(action._fields['statut'].selection).get(action.statut, action.statut) if action.statut else ''
                    sheet.write(row, 14, sit_action, cell_format)
                    sheet.write(row, 15, action.date_lancement.strftime('%d/%m/%Y') if action.date_lancement else '', date_format if action.date_lancement else cell_format)
                    sheet.write(row, 16, action.date_retour.strftime('%d/%m/%Y') if action.date_retour else '', date_format if action.date_retour else cell_format)
                    sheet.write(row, 17, action.duree_reelle or 0, cell_format)
                    sheet.write(row, 18, action.delai_jours or 0, cell_format)
                else:
                    for c in range(14, 19): sheet.write(row, c, '', cell_format)
                    
                sit_globale = dict(dossier._fields['etat_procedure'].selection).get(dossier.etat_procedure, dossier.etat_procedure) if dossier.etat_procedure else ''
                sheet.write(row, 19, sit_globale, cell_format)
                sheet.write(row, 20, dossier.date_leve_reserve.strftime('%d/%m/%Y') if dossier.date_leve_reserve else '', date_format if dossier.date_leve_reserve else cell_format)
                sheet.write(row, 21, dossier.date_delivrance.strftime('%d/%m/%Y') if dossier.date_delivrance else '', date_format if dossier.date_delivrance else cell_format)
                sheet.write(row, 22, dossier.delai_delivrance_act or 0, cell_format)
                sheet.write(row, 23, 30, cell_format)  # Délai réglementaire
                retard = max((dossier.delai_delivrance_act or 0) - 30, 0)
                sheet.write(row, 24, retard, cell_format)
                sheet.write(row, 25, "OUI" if retard <= 0 else "NON", cell_format)
                sheet.write(row, 26, dossier.observation_post_crui or '', cell_format)
                row += 1

        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())
        file_name = f"Situation_Projets_{self.date_passage.strftime('%d-%m-%Y')}.xlsx"
        
        self.write({'file_data': file_data, 'file_name': file_name})
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/situation.projet.wizard/{self.id}/file_data?download=true&filename={file_name}',
            'target': 'self',
        }