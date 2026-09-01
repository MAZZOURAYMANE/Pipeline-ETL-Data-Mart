import xmlrpc.client

URL = 'http://localhost:8069'

try:
    db_list_service = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/db')
    databases = db_list_service.list()
    print(f" Bases de données détectées sur Odoo : {databases}")
except Exception as e:
    print(f" Impossible de récupérer la liste des BDD : {e}")