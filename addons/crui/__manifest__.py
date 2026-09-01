# -*- coding: utf-8 -*-
{
    'name': "CRUI",

    'summary': """
        ce module permet la digitalisation du travail de la CRUI""",

    'description': """
        ce module permet la digitalisation du travail de la CRUI
    """,

    'author': "CRI Fès Meknès",
    'website': "https://www.fesmeknesinvest.ma",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Website',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hr'],

    # always loaded
    'data': [
        'security/crui_groups.xml',       # 1. groupes
        'security/crui_rules.xml',
        'security/ir.model.access.csv',
        'views/projet.xml',
        'views/secteur.xml',
        'views/macrosecteur.xml',
        'views/commune.xml',
        'views/prefecture.xml',
        'views/soumission.xml',
        'views/enquete.xml',
        'views/foncier.xml',
        'views/act.xml',
        'views/action.xml',
        'views/dossier.xml',
        'views/spoc.xml',
        'views/dashboard.xml',
        'views/visite.xml',
        'views/bilan.xml',
        'views/menu-items.xml',
        'views/projet_dashboard_graph.xml',
        'wizards/ordre_jour_wizard_view.xml',
        'wizards/situation_projet_wizard_view.xml',
        'wizards/fiche_crui_wizard_view.xml',
        'data/cron.xml',
        'data/demo_projet_data.xml',

    ],
    'images': ['static/description/icon.png'], 
    # only loaded in demonstration mode
    'demo': [
    ],
    'licence': "LGPL-3",
    'application':True,
}
