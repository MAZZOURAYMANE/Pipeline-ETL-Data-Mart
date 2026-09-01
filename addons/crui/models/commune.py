from odoo import models, fields, api


class Commune (models.Model):
    _name ='commune'
    _description = 'Commune'
    name = fields.Char(string='commune')