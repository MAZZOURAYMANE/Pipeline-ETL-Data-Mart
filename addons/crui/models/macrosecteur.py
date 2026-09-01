from odoo import models, fields, api


class Secteur(models.Model):
    _name = 'secteur'
    _description = 'secteur d\'investissement'
    name = fields.Char(
        string='Secteur',
        required=True
    )