from odoo import models, fields, api


class Act(models.Model):
    _name = 'act'
    _description = 'Acts CRUI'

    name = fields.Char(string='Act')