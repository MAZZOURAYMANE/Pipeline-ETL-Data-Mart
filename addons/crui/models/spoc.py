from odoo import models, fields, api


class Conseiller(models.Model):
    _name = 'conseiller'
    _description = 'SPOC'

    spoc_id = fields.Many2one("res.users",string='Nom du SPOC')
    prenom = fields.Char(string='Prénom du SPOC',related= "spoc_id.name")
    email = fields.Char(string='Email du SPOC',related= "spoc_id.email")
