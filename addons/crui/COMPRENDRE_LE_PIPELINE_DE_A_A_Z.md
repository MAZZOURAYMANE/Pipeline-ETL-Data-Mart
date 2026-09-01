# 🧭 GUIDE COMPLET : COMPRENDRE LE PROJET ET LE PIPELINE DE A À Z
## Plateforme Décisionnelle & Gouvernance des Données — CRI Fès-Meknès

---

## 🌟 Introduction : Quelle était l'histoire au départ ?

### 1. Le Contexte Métier
Au **Centre Régional d'Investissement (CRI) Fès-Meknès**, les investisseurs déposent des projets (usines, hôtels, fermes agricoles, etc.). Ces projets passent devant la **Commission Régionale Unifiée d'Investissement (CRUI)**.
* Les conseillers du CRI utilisent **Odoo 16** (un ERP) pour saisir les dossiers, les montants en Dirhams, les prévisions d'emplois, les avis des commissions, les dates de dépôt, etc.

### 2. Le Problème
1. **Odoo est un système transactionnel (OLTP) :** Il est conçu pour la saisie quotidienne rapide (1 formulaire à la fois), **pas pour faire des statistiques lourdes** ou des calculs de tendances sur 5 ans. Si la direction lance des requêtes d'analyse lourdes directement sur Odoo, cela ralentit l'ERP pour tous les conseillers.
2. **Qualité des données dégradée :** Avec le temps, les utilisateurs ont créé des variantes (`Fès`, `FES`, `F-s`, `feq`), des textes de dossiers collés dans les communes, et des numéros de parcelles enregistrés comme types fonciers.
3. **Absence d'automatisation décisionnelle :** Impossible de savoir en temps réel si les dossiers respectent la **Loi 47-18** (délai légal maximum de **30 jours** pour traiter un dossier).

---

## 🗺️ Le Voyage d'une Donnée : Du Clic dans Odoo jusqu'au Tableau de Bord

Voici le schéma global et simple du pipeline :

```
 ┌─────────────┐       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
 │   ÉTAPE 1   │       │   ÉTAPE 2   │       │   ÉTAPE 3   │       │   ÉTAPE 4   │       │   ÉTAPE 5   │
 │  Odoo ERP   │ ───►  │ Airbyte CDC │ ───►  │  Data Lake  │ ───►  │  Warehouse  │ ───►  │   dbt Core  │ ───► 📊 BI & DBeaver
 │ (PostgreSQL)│       │ (Ingestion) │       │ (MinIO S3)  │       │ (Bronze Raw)│       │(Silver/Gold)│     (Data Marts)
 └─────────────┘       └─────────────┘       └─────────────┘       └─────────────┘       └─────────────┘
        ▲                                                                                       │
        │                                                                                       │
        └────────────────────────── 🤖 APACHE AIRFLOW (Chef d'Orchestre) ───────────────────────┘
```

---

## 🔍 Explication Détaillée Étape par Étape

---

### 📍 ÉTAPE 1 : La Source — Odoo ERP & PostgreSQL
* **Ce qui s'y passe :** Un conseiller crée ou modifie un projet dans Odoo (ex: *Atlas Packaging, 55 MDH, 135 emplois*).
* **Le Mécanisme Clé (CDC - Change Data Capture) :**
  - Au lieu de faire un `SELECT * FROM projet` toutes les heures (ce qui fatigue la base), PostgreSQL enregistre chaque modification dans un journal binaire interne appelé **WAL (*Write-Ahead Log*)**.
  - Nous avons activé `wal_level = logical` et créé une publication SQL couvrant les **23 tables métiers** avec un slot de réplication nommé `airbyte_slot`.
  - **Résultat :** Zéro ralentissement sur Odoo. Dès qu'une ligne bouge, elle est prête à être capturée.

---

### 📍 ÉTAPE 2 : Le Transporteur — Airbyte OSS
* **Son Rôle :** C'est le "coursier" automatique du système.
* **Comment il fonctionne :**
  - Airbyte se connecte au port PostgreSQL d'Odoo et lit en temps réel le flux des changements (CDC).
  - Il extrait les données modifiées, les convertit en format structuré **JSON Lines (`.jsonl.gz`)**, et les expédie vers le stockage objet.
  - **Identifiant de la connexion configurée :** `fadaefb4-acb1-420d-8656-c9e23394a9e2`.

---

### 📍 ÉTAPE 3 : Le Coffre-Fort — Data Lake MinIO (S3)
* **Pourquoi ajouter MinIO au milieu ?**
  1. **Archive brute immuable :** Même si quelqu'un supprime accidentellement un projet dans Odoo, le fichier JSON brut reste stocké dans MinIO pour toujours.
  2. **Rejouabilité :** Si on change notre modèle de données dans 6 mois, on peut recalculer tout l'historique depuis MinIO sans jamais retoucher à la base Odoo.
  3. **Stockage futur des fichiers lourds :** Plans de masse, fiches PDF, PVs de commission.
* **Emplacement :** Bucket S3 `s3://crui-raw/`.

---

### 📍 ÉTAPE 4 : L'Atterrissage — Ingestion Bronze dans le Data Warehouse
* **Ce qui s'y passe :**
  - Un script Python développé sur mesure ([`crui_dbt/scripts/load_minio_to_warehouse.py`](./crui_dbt/scripts/load_minio_to_warehouse.py)) se réveille.
  - Il télécharge les fichiers JSONL depuis MinIO, les décompresse, et les injecte dans la base PostgreSQL analytique `warehouse-db` (Port **5433**).
  - Ces données atterrissent dans la **Couche Bronze (Schéma `raw_odoo`)** qui contient les 12 tables sources : `projet`, `dossier`, `enquete`, `prefecture`, `commune`, `foncier`, `secteur`, `macrosecteur`, `act`, `res_partner`, `res_users`, `soumission`.

---

### 📍 ÉTAPE 5 : La Transformation — dbt Core (Architecture Medallion)
**dbt (*data build tool*)** est l'usine de transformation de la donnée. Il prend la donnée brute et la transforme en or décisionnel à travers 3 couches successives :

```
┌───────────────────────────┐     ┌───────────────────────────┐     ┌───────────────────────────┐
│      BRONZE (Raw)         │     │      SILVER (Staging)     │     │       GOLD (Marts)        │
│   12 Tables brutes Odoo   │ ──► │  3 Vues SQL Standardisées │ ──► │ 4 Tables Schéma en Étoile │
│   (schéma raw_odoo)       │     │  (schéma public_staging)  │     │   (schéma public_marts)   │
└───────────────────────────┘     └───────────────────────────┘     └───────────────────────────┘
```

1. **Couche Bronze (`raw_odoo`) :** Données brutes telles quelles (textes, chaînes brutes).
2. **Couche Silver (`public_staging`) :**
   - Vues SQL de nettoyage : `stg_projet`, `stg_dossier`, `stg_enquete`.
   - **Ce qu'on y fait :** Typage des dates (`timestamp`), conversion des montants numériques (`numeric`), traitement des textes vides (`NULLIF`).
3. **Couche Gold (`public_marts`) — Le Schéma en Étoile (Star Schema) :**
   - **2 Dimensions (Le Contexte) :**
     - `dim_project` : Caractéristiques de chaque investissement (nom, raison sociale, province, commune, secteur, foncier).
     - `dim_date` : Calendrier complet (années, trimestres, mois, jours ouvrés).
   - **2 Tables de Faits (Les Mesures Métiers) :**
     - `fct_dossier_processing` : Mesure les délais d'instruction de la CRUI (délai en jours ouvrés, respect du seuil légal de 30 jours `is_submitted_within_30j`, avis favorable).
     - `fct_project_followup` : Mesure la réalisation sur le terrain (montant investi réel vs prévu, emplois créés réels vs prévus, % d'avancement).

---

### 📍 ÉTAPE 6 : La Gouvernance & le Nettoyage des Données
Pour que les tableaux de bord soient justes, nous avons assaini la base Odoo :
* **Bilan du nettoyage :** Passage de **659 entrées bruitées** à **80 entrées officielles** (**-87,8 % de bruit**).
* **Nomenclatures officielles arrêtées :**
  - **9** Préfectures et Provinces de la Région Fès-Meknès.
  - **29** Communes territoriales régionales.
  - **16** Secteurs d'activité alignés avec **8** Macro-secteurs nationaux.
  - **8** Régimes fonciers marocains (Melk, Domanial, Soulaliyate, Habous...).
  - **10** Actes administratifs CRUI.
* **Intégrité :** Les **1 123 projets** existants ont été automatiquement réaffectés vers les nouveaux identifiants sans aucune perte.

---

### 📍 ÉTAPE 7 : L'Automatisation — Apache Airflow
* **Son Rôle :** Le chef d'orchestre automatique.
* **Son Planning :** Chaque nuit à **02h00 du matin**, Airflow déclenche le DAG `crui_lakehouse_pipeline.py` qui exécute en chaîne :
  1. `trigger_airbyte_sync` : Lance la synchronisation Airbyte CDC vers MinIO.
  2. `load_minio_to_warehouse` : Télécharge le S3 et charge le schéma `raw_odoo`.
  3. `dbt_run` : Compile et régénère les 7 modèles de Staging et de Data Marts.
  4. `dbt_test` : Vérifie automatiquement l'intégrité (clés uniques, non-null, relations).

---

### 📍 ÉTAPE 8 : L'Exploitation Finale — Décideurs & BI
Le matin à 08h00, quand la Direction du CRI ou les analystes ouvrent leur outil décisionnel (Power BI, DBeaver, Apache Superset) connecté sur le port `5433` :
- Tous les graphiques sont à jour.
- Ils voient en un coup d'œil :
  - Le montant total d'investissement par province (ex: Fès 55 MDH, Ifrane 82 MDH).
  - Le taux de dossiers instruits dans le délai légal des 30 jours.
  - Le nombre réel d'emplois créés par secteur.

---

## 🎯 Synthèse des Technologies Utilisées

| Brique | Outil | Port / Accès | Rôle dans le Projet |
| :--- | :--- | :--- | :--- |
| **Source OLTP** | Odoo 16 + PostgreSQL | `8069` / `5434` | Gestion opérationnelle des projets d'investissement |
| **Ingestion CDC** | Airbyte OSS | `8000` | Capture asynchrone des modifications |
| **Data Lake S3** | MinIO Object Storage | `9000` / `9001` | Stockage objet immuable & historique JSONL |
| **Data Warehouse**| PostgreSQL 15 | `5433` | Entrepôt analytique (Bronze `raw_odoo` / Gold `public_marts`) |
| **Transformation**| dbt Core | CLI / Scripts | Modélisation dimensionnelle Medallion & Tests qualité |
| **Orchestrateur** | Apache Airflow 2.7.1 | `8080` | Planification quotidienne & monitoring automatique |
| **Visualisation** | DBeaver & HTML ERD | Client / Fichier | Exploration visuelle du schéma en étoile et reporting |
