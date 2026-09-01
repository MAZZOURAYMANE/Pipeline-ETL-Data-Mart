from odoo import models, fields, api

class Prefecture(models.Model):
    _name= 'prefecture'
    _description = 'refecture & province'
    name = fields.Char(string="Préfécture ou Province")