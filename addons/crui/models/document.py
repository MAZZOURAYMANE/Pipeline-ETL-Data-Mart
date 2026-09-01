from odoo import models, fields, api


class Document(models.Model):
    _name = 'docuement'
    _description = 'Documents CRUI CRUI'

    name = fields.Char(string='Document')