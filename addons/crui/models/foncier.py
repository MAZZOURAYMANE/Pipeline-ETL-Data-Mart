from odoo import models, fields, api


class Foncier (models.Model):
    _name = 'foncier'
    _description= "nature du foncier"
    name = fields.Char(string= 'Foncier')