from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
from io import BytesIO
from odoo.tools.misc import xlsxwriter
import logging

_logger = logging.getLogger(__name__)


class OrdreJourWizard(models.TransientModel):
    _name = 'ordre.jour.wizard'
    _description = 'Wizard pour générer l\'ordre du jour XLSX'

    date_passage = fields.Date(
        string="Date de passage CRUI",
        required=True,
        help="Sélectionnez la date de passage pour générer l'ordre du jour"
    )

    file_data = fields.Binary(
        string="Fichier généré",
        readonly=True
    )

    file_name = fields.Char(
        string="Nom du fichier",
        readonly=True
    )

    def action_generate_ordre_jour(self):
        """Génère l'ordre du jour XLSX basé sur la date de passage sélectionnée"""
        self.ensure_one()

        if not self.date_passage:
            raise UserError("Veuillez sélectionner une date de passage.")

        # Rechercher tous les dossiers avec cette date de passage et statut CRUI
        # Utilisation de sudo() pour inclure les dossiers de tous les utilisateurs
        dossiers = self.env['dossier'].sudo().search([
            ('date_passage', '>=', fields.Datetime.to_string(
                fields.Datetime.from_string(str(self.date_passage) + ' 00:00:00')
            )),
            ('date_passage', '<=', fields.Datetime.to_string(
                fields.Datetime.from_string(str(self.date_passage) + ' 23:59:59')
            )),
            ('statut_dossier', '=', 'crui')
        ])

        if not dossiers:
            raise UserError(f"Aucun dossier trouvé pour la date {self.date_passage.strftime('%d/%m/%Y')}.")

        # Récupérer les projets associés et trier par préfecture, puis par acte
        projets_data = []
        for dossier in dossiers:
            projet = dossier.projet_id
            if projet:
                # Récupérer la localisation (commune uniquement)
                localisation = ""
                if projet.commune_id and projet.commune_id.name:
                    localisation = f"Commune de {projet.commune_id.name}"

                # Log pour déboguer
                _logger.info(f"Projet {projet.identifiant_projet or projet.id}: prefecture={projet.prefecture_id.name if projet.prefecture_id else 'None'}, commune={projet.commune_id.name if projet.commune_id else 'None'}, localisation='{localisation}'")

                # Récupérer les actes demandés
                actes = ", ".join(dossier.actes_ids.mapped('name')) if dossier.actes_ids else ""

                # Convertir le montant d'investissement en millions de dirhams
                mt_invest_mdh = projet.montant_investissement / 1000000 if projet.montant_investissement else 0

                # Vérifier si le projet a déjà été programmé en CRUI avant cette date
                dossiers_anterieurs = self.env['dossier'].search([
                    ('projet_id', '=', projet.id),
                    ('statut_dossier', '=', 'crui'),
                    ('date_passage', '<', dossier.date_passage),
                    ('id', '!=', dossier.id)
                ], order='date_passage desc')

                # Construire l'observation avec historique des passages précédents
                observations = []
                if dossier.observation_post_crui:
                    observations.append(dossier.observation_post_crui)

                if dossiers_anterieurs:
                    passages_info = []
                    for doss_ant in dossiers_anterieurs:
                        if doss_ant.date_passage:
                            date_formattee = doss_ant.date_passage.strftime('%d/%m/%Y')
                            decision = doss_ant.decision_crui or "Décision non renseignée"
                            passages_info.append(f"du {date_formattee} : {decision}")

                    if passages_info:
                        historique = f"Historique du projet : Projet examiné par la CRUI {', '.join(passages_info)}"
                        observations.append(historique)

                observation_finale = " - ".join(observations) if observations else ""

                projets_data.append({
                    'projet': projet,
                    'dossier': dossier,
                    'prefecture': projet.prefecture_id.name if projet.prefecture_id else "",
                    'localisation': localisation,
                    'actes': actes,
                    'mt_invest_mdh': mt_invest_mdh,
                    'observations': observation_finale,
                })

        # Grouper par préfecture puis par acte
        from collections import defaultdict
        grouped_data = defaultdict(lambda: defaultdict(list))

        for data in projets_data:
            prefecture = data['prefecture'] or "Hors Plateforme"
            actes = data['actes'] or "Non spécifié"
            grouped_data[prefecture][actes].append(data)

        # Ordre personnalisé des préfectures/provinces
        ordre_prefectures = [
            'FES',
            'MOULAY YACOUB',
            'SEFROU',
            'BOULEMANE',
            'TAOUNATE',
            'TAZA',
            'EL HAJEB',
            'IFRANE',
            'MEKNES',
        ]

        # Distinguer préfectures vs provinces
        prefectures = ['FES', 'MEKNES']

        # Trier les préfectures selon l'ordre défini
        sorted_prefectures = []
        for pref in ordre_prefectures:
            if pref in grouped_data:
                sorted_prefectures.append(pref)

        # Ajouter les préfectures non listées (ex: "Hors Plateforme")
        for pref in grouped_data.keys():
            if pref not in sorted_prefectures:
                sorted_prefectures.append(pref)

        # Générer le fichier XLSX
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Ordre du jour')

        # Définir les formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True
        })

        prefecture_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FFF2CC',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 12
        })

        acte_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E7E6E6',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11
        })

        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'top',
            'text_wrap': True
        })

        number_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        # Définir les colonnes
        columns = [
            ('N°', 5),
            ('Id', 15),
            ('Référence', 15),
            ('Intitulé du Projet', 40),
            ('Localisation', 25),
            ('Porteur du Projet/Raison Sociale', 30),
            ('Mt Invest MDh', 15),
            ("Nbr d'emplois à créer", 15),
            ('Surface du terrain', 20),
            ('Observations', 30)
        ]

        # Écrire les en-têtes
        for col_num, (col_name, col_width) in enumerate(columns):
            worksheet.write(0, col_num, col_name, header_format)
            worksheet.set_column(col_num, col_num, col_width)

        # Écrire les données groupées
        row_num = 1
        global_idx = 1

        for prefecture in sorted_prefectures:
            # Écrire l'en-tête de préfecture avec le préfixe approprié
            if prefecture == "Hors Plateforme":
                prefecture_label = prefecture
            elif prefecture in prefectures:
                # C'est une préfecture (FES ou MEKNES)
                prefecture_label = f"Préfecture de {prefecture}"
            else:
                # C'est une province
                prefecture_label = f"Province de {prefecture}"
            worksheet.merge_range(row_num, 0, row_num, 9, prefecture_label, prefecture_format)
            row_num += 1

            # Trier les actes dans cette préfecture
            sorted_actes = sorted(grouped_data[prefecture].keys())

            for acte in sorted_actes:
                # Écrire l'en-tête d'acte
                worksheet.merge_range(row_num, 0, row_num, 9, acte, acte_format)
                row_num += 1

                # Écrire les projets pour cet acte
                for data in grouped_data[prefecture][acte]:
                    projet = data['projet']
                    dossier = data['dossier']

                    worksheet.write(row_num, 0, global_idx, number_format)  # N°
                    worksheet.write(row_num, 1, projet.identifiant_projet or '', cell_format)  # Id
                    worksheet.write(row_num, 2, projet.reference or '', cell_format)  # Référence
                    worksheet.write(row_num, 3, projet.name or '', cell_format)  # Intitulé du Projet
                    worksheet.write(row_num, 4, data['localisation'], cell_format)  # Localisation
                    worksheet.write(row_num, 5, projet.raison_social or projet.petitionnaire or '', cell_format)  # Porteur
                    worksheet.write(row_num, 6, f"{data['mt_invest_mdh']:.2f}", cell_format)  # Mt Invest MDh
                    worksheet.write(row_num, 7, projet.nombre_emploi or 0, number_format)  # Nbr d'emplois
                    worksheet.write(row_num, 8, projet.surface or '', cell_format)  # Surface
                    worksheet.write(row_num, 9, data['observations'], cell_format)  # Observations avec historique

                    row_num += 1
                    global_idx += 1

        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())

        # Générer le nom du fichier
        date_str = self.date_passage.strftime('%d-%m-%Y')
        file_name = f"Ordre_du_jour_{date_str}.xlsx"

        # Enregistrer le fichier dans le wizard
        self.write({
            'file_data': file_data,
            'file_name': file_name
        })

        # Retourner une action pour télécharger le fichier
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/ordre.jour.wizard/{self.id}/file_data?download=true&filename={file_name}',
            'target': 'self',
        }
