# 📖 Récapitulatif Complet de la Session de Travail – Projet Data CRUI
*Fichier de sauvegarde généré le 25 Août 2026*  
*Projet : Plateforme Data & Ingestion Odoo CRUI (CRI Fès-Meknès)*

---

## 📌 Sommaire des Thématiques Abordées

1. [Génération du Jeu de Données de Test (Odoo CRUI)](#1-génération-du-jeu-de-données-de-test-odoo-crui)
2. [Résolution de l'Erreur de Commande et Mise à Jour Docker](#2-résolution-de-lerreur-de-commande-et-mise-à-jour-docker)
3. [Explication sur Airbyte (`0 loaded`) et Synchronisation CDC](#3-explication-sur-airbyte-0-loaded-et-synchronisation-cdc)
4. [Évaluation de l'État d'Avancement du Pipeline Data](#4-évaluation-de-létat-davancement-du-pipeline-data)
5. [Compréhension de la Modélisation SQL avec dbt (Architecture Medallion)](#5-compréhension-de-la-modélisation-sql-avec-dbt-architecture-medallion)
6. [Résolution des Erreurs dbt (`dbt` non reconnu & `relation raw_odoo does not exist`)](#6-résolution-des-erreurs-dbt)
7. [Configuration de la Source et Destination dans Airbyte](#7-configuration-de-la-source-et-destination-dans-airbyte)
8. [Rôle de MinIO (Data Lake) vs Connexion Directe au Data Warehouse](#8-rôle-de-minio-data-lake-vs-connexion-directe-au-data-warehouse)

---

## 1. Génération du Jeu de Données de Test (Odoo CRUI)

### Besoin initial :
Peupler la page formulaire et la liste du modèle `projet` dans Odoo avec des données complètes, réalistes et cohérentes avec la région Fès-Meknès.

### Réalisations :
- **Fichier créé :** [`data/demo_projet_data.xml`](./data/demo_projet_data.xml)
- **Fichier mis à jour :** [`__manifest__.py`](./__manifest__.py) (chargement automatique via la liste `data`).
- **Données insérées :**
  - **4 Préfectures/Provinces :** Fès, Meknès, Sefrou, Ifrane.
  - **5 Communes :** Fès-Agdal, Fès-Médina, Meknès-Hamria, Aïn Cheggag, Ifrane.
  - **Macro-secteurs & Secteurs :** Industrie, Tourisme, Agro-industrie, Offshoring/BPO.
  - **Types de Fonciers & Actes CRUI :** Parc Industriel ZAE, Melk Privé, Permis de construire, Dérogations.
  - **Pétitionnaires (Entreprises) :** Atlas Packaging SARL, Société Cèdre Resort SA, Saïss Bio Huiles SARL.
  - **4 Projets complets à différents stades :**
    1. `PRJ-2024-FES-001` : **Atlas Packaging SARL** (*Traitement CRUI* – 55 MDH – 135 emplois).
    2. `PRJ-2024-IFR-004` : **Société Cèdre Resort SA** (*Traitement SPOC* – 82 MDH – 90 emplois).
    3. `PRJ-2024-SEF-012` : **Saïss Bio Huiles SARL** (*Nouveau* – 28.5 MDH – 45 emplois).
    4. `PRJ-2023-FES-078` : **Tech Park Fès SA** (*Clôturé / Opérationnel* – 32 MDH – 350 emplois).

---

## 2. Résolution de l'Erreur de Commande et Mise à Jour Docker

### Problème rencontré :
```text
odoo-bin : Le terme «odoo-bin» n'est pas reconnu...
```
### Cause & Solution :
Odoo ne tourne pas directement sur Windows, mais dans un conteneur Docker (`odoo-docker-web-1`).  
La commande de mise à jour a été exécutée directement à l'intérieur du conteneur :
```bash
docker exec odoo-docker-web-1 odoo -u crui -d dev_db --stop-after-init
docker restart odoo-docker-web-1
```

---

## 3. Explication sur Airbyte (`0 loaded`) et Synchronisation CDC

### Question :
Pourquoi Airbyte affichait-il `0 loaded` après l'ajout des projets dans Odoo ?

### Explication :
Airbyte ne charge pas les données en continu sans déclencheur. Il fonctionne par **Jobs de synchronisation (Syncs)**. Tant qu'un Sync n'a pas été déclenché après l'insertion dans Odoo, le compteur reste sur le dernier état.
- **Solution :** Se rendre sur `http://localhost:8000` > **Connections** > Cliquer sur **Sync now**.

---

## 4. Évaluation de l'État d'Avancement du Pipeline Data

Un document complet de reporting managérial et technique a été rédigé :  
📄 **[`ETAT_AVANCEMENT_PROJET.md`](./ETAT_AVANCEMENT_PROJET.md)**

### Synthèse des jalons :
- **Source Odoo & Données :** 🟢 100%
- **CDC PostgreSQL (`wal_level=logical`, slot `airbyte_slot`, publication 23 tables) :** 🟢 100%
- **Airbyte Ingestion :** 🟢 100%
- **Data Lake MinIO (`s3://crui-raw/`) :** 🟢 100%
- **Modélisation dbt Core :** 🟡 85%
- **PostgreSQL Warehouse (`warehouse-db`) :** 🟡 60%
- **Orchestration Airflow :** 🔴 15%
- **BI / Dashboards :** 🔴 0%

---

## 5. Compréhension de la Modélisation SQL avec dbt (Architecture Medallion)

La transformation repose sur l'**Architecture Medallion (Bronze ➔ Silver ➔ Gold)** :

```
[Couche RAW (Bronze)]         ──▶   [Couche STAGING (Silver)]      ──▶   [Couche MARTS (Gold)]
Tables brutes Airbyte               Nettoyage & Typage                  Schéma en Étoile (Star Schema)
(odoo_raw.projet, dossier...)       (stg_projet, stg_dossier...)        (dim_project, fct_dossier...)
```

- **Couche Staging (Silver) :** Standardisation des noms de colonnes, cast des types de données, gestion des valeurs nulles.
- **Couche Marts (Gold) :**
  - **Dimensions :** `dim_project`, `dim_date` (dénormalisation avec noms des communes, préfectures, pétitionnaires).
  - **Faits :** `fct_dossier_processing` (délais SPOC et CRUI en jours ouvrés), `fct_project_followup` (suivi réel vs prévu).

---

## 6. Résolution des Erreurs dbt

### Erreur 1 : `dbt n'est pas reconnu`
- **Solution :** Installation du package dbt pour PostgreSQL :
  ```powershell
  pip install dbt-postgres
  ```

### Erreur 2 : `relation "raw_odoo.dossier" does not exist`
- **Cause :** dbt cherche les tables sources dans le schéma `raw_odoo` de la base `warehouse-db`, or ce schéma n'avait pas encore été créé/peuplé par Airbyte.
- **Solution :** Configurer la destination Postgres dans Airbyte avec le schéma par défaut `raw_odoo` et lancer la synchronisation.

---

## 7. Configuration de la Source et Destination dans Airbyte

### Paramètres de la Source Postgres (Odoo CDC) :
- **Host :** `host.docker.internal` | **Port :** `5434` | **Database :** `dev_db`
- **User :** `odoo` | **Password :** `odoo` | **SSL Mode :** `disable`
- **Replication Method :** `CDC`
- **Replication Slot :** `airbyte_slot`
- **Publication :** `airbyte_publication`

### Paramètres de la Destination Postgres (Warehouse) :
- **Host :** `host.docker.internal` | **Port :** `5433` | **Database :** `warehouse`
- **User :** `analytical_user` | **Password :** `analytical_password_secret`
- **Destination Namespace :** `Custom Format` ➔ `raw_odoo`

---

## 8. Rôle de MinIO (Data Lake) vs Connexion Directe au Data Warehouse

| Fonctionnalité | Destination Directe Postgres Warehouse | Destination MinIO (Object Storage S3) |
| :--- | :--- | :--- |
| **Objectif principal** | Alimenter immédiatement les modèles dbt et les dashboards BI. | Conserver une archive brute, immuable et horodatée de tous les événements CDC. |
| **Gestion des documents** | Moins adaptée aux gros volumes de fichiers binaires. | Idéale pour stocker les plans de masse, fiches PDF et PVs CRUI. |
| **Rejouabilité / Audit** | Les tables sont modifiées par dbt. | Historique complet rejouable à l'infini en cas de sinistre ou refonte. |

> 💡 **Recommandation :** Utiliser la destination directe Postgres pour la transformation dbt immédiate, tout en conservant le bucket MinIO `crui-raw` comme Data Lake d'archivage.
