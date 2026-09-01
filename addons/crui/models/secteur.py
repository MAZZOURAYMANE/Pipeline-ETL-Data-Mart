from odoo import models, fields, api


class Secteur(models.Model):
    _name = 'macrosecteur'
    _description = 'marcosecteur d\'investissement'
    name = fields.Char(
        string='MacroSecteur',
        required=True
    )