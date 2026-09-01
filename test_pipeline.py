import xmlrpc.client
import json
from kafka import KafkaProducer

# 1. PARAMÈTRES DE CONNEXION
URL = 'http://localhost:8069'
DB = 'dev_db'       # Nom de la BDD défini dans ton docker-compose
USER = 'aymanemazzour@gmail.com'        # Login Odoo
PASSWORD = 'Aymane1234'    # Mot de passe Odoo (modifie si besoin)
KAFKA_BROKER = 'localhost:9092'
TOPIC_TEST = 'odoo-test-native'

print("1. Connexion à Odoo...")
try:
    # Authentification auprès du serveur Odoo
    common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
    uid = common.authenticate(DB, USER, PASSWORD, {})
    
    if not uid:
        print(" Échec d'authentification : Vérifie le nom de la BDD, le login ou le mot de passe.")
        exit()
        
    print(f" Authentification réussie dans Odoo (UID Utilisateur: {uid})")

    # 2. LECTURE D'UNE TABLE NATIVE (res.users)
    print("\n2. Lecture des utilisateurs par défaut d'Odoo...")
    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')
    users_data = models.execute_kw(
        DB, uid, PASSWORD,
        'res.users', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'login'], 'limit': 5}
    )
    print(f" Données système récupérées d'Odoo : {users_data}")

    # 3. ENVOI VERS APACHE KAFKA
    print("\n3. Connexion à Kafka et envoi du message...")
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    for user in users_data:
        producer.send(TOPIC_TEST, value=user)

    producer.flush()
    print(f" Succès ! Données transmises au topic Kafka '{TOPIC_TEST}'.")

except Exception as e:
    print(f"\n Erreur rencontrée : {e}")