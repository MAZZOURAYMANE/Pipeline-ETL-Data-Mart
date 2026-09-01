# 📄 RÉSUMÉ DU RAPPORT DE STAGE (FRANÇAIS & ANGLAIS)

---

## 🇫🇷 Résumé (Français)

Le présent rapport est la synthèse d’un projet intitulé **« Mise en place d’un cadre de gouvernance de données et déploiement d’un pipeline ETL / Data Mart »**, réalisé au sein du **Centre Régional d’Investissement Fès-Meknès (CRI)** dans le cadre d’un stage de fin d’année, filière **Génie Informatique** à l’**Université Privée de Fès (UPF)**, pour une durée de **2 mois**.

Dans un contexte marqué par la transformation digitale et l'application des dispositions de la **Loi 47-18** régissant les Centres Régionaux d’Investissement, la **Commission Régionale Unifiée d’Investissement (CRUI)** traite un volume stratégique de données relatives aux projets d’investissement régionaux. Toutefois, le système d'information opérationnel (ERP Odoo) faisait face à des défis majeurs d'hétérogénéité, de prolifération de doublons et d'absence de mécanismes de reporting analytique automatisé.

L’objectif principal de ce stage a été de concevoir et d'implémenter une solution décisionnelle moderne de bout en bout couplée à un cadre robuste de gouvernance des données :

1. **Gouvernance et Qualité des Données (*Data Governance & MDM*) :** Diagnostic de la qualité selon le référentiel DAMA-DMBOK, standardisation des nomenclatures officielles régionales et nationales (9 provinces, 29 communes, 16 secteurs, 8 macro-secteurs, 8 régimes fonciers, 10 actes administratifs) et assainissement curatif de la base ayant permis d'éliminer **87,8 % du bruit** tout en préservant l'intégrité de **1 123 projets**.
2. **Déploiement du Pipeline ETL/ELT & Lakehouse :** Mise en place d'une chaîne de données moderne intégrant la capture des changements en temps réel (**Change Data Capture - CDC via Airbyte OSS** depuis PostgreSQL), l'archivage immuable sur un **Data Lake S3 (MinIO)**, la modélisation en couches Medallion (*Bronze ➔ Silver ➔ Gold*) avec **dbt Core**, et l'orchestration automatisée sous **Apache Airflow**.
3. **Modélisation Dimensionnelle & Data Marts :** Conception d’un schéma en étoile selon la méthode Kimball au sein d'un entrepôt PostgreSQL analytique, intégrant des tables de dimensions (`dim_project`, `dim_date`) et des tables de faits (`fct_dossier_processing`, `fct_project_followup`) pour le calcul automatisé des indicateurs clés (respect du délai légal de 30 jours, volume d'investissement par province et suivi des créations d'emplois).

Ce projet offre ainsi au CRI Fès-Meknès une plateforme décisionnelle agile, sécurisée et pérenne, garantissant la fiabilité des données et fournissant aux décideurs des indicateurs précis pour le pilotage économique régional.

**Mots-clés :** Gouvernance des Données, Data Quality, Master Data Management (MDM), Pipeline ETL/ELT, Change Data Capture (CDC), Data Lakehouse, dbt Core, Apache Airflow, Data Mart, Schéma en Étoile, CRI Fès-Meknès, Odoo ERP.

---

## 🇬🇧 Abstract (English)

This report summarizes the project entitled **"Implementation of a Data Governance Framework and Deployment of an ETL Pipeline / Data Mart"**, carried out at the **Regional Investment Center of Fès-Meknès (CRI)** as part of an end-of-year internship in **Computer Engineering** at the **Private University of Fès (UPF)**, over a duration of **2 months**.

In the context of regional digital transformation and the enforcement of **Law 47-18** reforming Regional Investment Centers, the Unified Regional Investment Commission (CRUI) processes crucial data regarding regional investment initiatives. However, the operational information system (Odoo ERP) suffered from data heterogeneity, duplicate entries, and a lack of automated analytical reporting.

The primary objective of this internship was to design and deploy an end-to-end Modern Data Stack coupled with a solid data governance framework:

1. **Data Governance & Quality Management:** Executing data quality assessments based on the DAMA-DMBOK framework, standardizing Master Data Management (MDM) nomenclatures (9 provinces, 29 municipalities, 16 business sectors, 8 macro-sectors, 8 land tenures, 10 administrative acts), and eliminating **87.8% of data noise** while preserving the referential integrity of **1,123 existing investment projects**.
2. **ETL/ELT Pipeline & Lakehouse Deployment:** Implementing a Modern Data Stack leveraging near real-time **Change Data Capture (CDC via Airbyte OSS)** on PostgreSQL WAL logs, immutable object storage on an **S3 Data Lake (MinIO)**, modular Medallion transformations (*Bronze ➔ Silver ➔ Gold*) with **dbt Core**, and daily workflow orchestration using **Apache Airflow**.
3. **Dimensional Modeling & Data Marts:** Developing a Kimball star schema within an analytical PostgreSQL warehouse featuring dimension tables (`dim_project`, `dim_date`) and fact tables (`fct_dossier_processing`, `fct_project_followup`) for automated tracking of critical KPIs (compliance with the 30-day legal processing threshold, investment volumes, and job creation rates).

This project equips CRI Fès-Meknès with a scalable, secure, and reliable decision-support platform, empowering stakeholders with high-integrity analytics for regional economic development.

**Keywords:** Data Governance, Data Quality, Master Data Management (MDM), ETL/ELT Pipeline, Change Data Capture (CDC), Data Lakehouse, dbt Core, Apache Airflow, Data Mart, Star Schema, CRI Fès-Meknès, Odoo ERP.
