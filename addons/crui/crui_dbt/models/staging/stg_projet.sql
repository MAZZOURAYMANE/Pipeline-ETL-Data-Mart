-- stg_projet.sql
-- Silver Layer: Cleans and standardizes the raw projet table from Odoo.

with source as (
    select * from {{ source('odoo_raw', 'projet') }}
),

cleaned as (
    select
        id                                          as projet_id,
        identifiant_projet,
        reference,
        name                                        as projet_name,
        statut                                      as statut_projet,
        consistance,
        composante,
        raison_social,
        forme_juridique,
        surface,
        reference_fonciere,
        dispositions_urbanistiques,
        annee,

        -- Foreign Keys
        petitionnaire_id                            as partner_id,
        prefecture_id,
        commune_id,
        foncier_id,
        conseiller_id                               as spoc_user_id,

        -- Financial KPIs
        cast(montant_investissement as numeric)     as montant_investissement,
        cast(nombre_emploi as integer)              as nombre_emploi,
        cast(duree_projet as integer)               as duree_projet_days,

        -- Timestamps (for CDC tracking)
        cast(nullif(date_lancement, '') as timestamp)   as date_lancement,
        cast(nullif(date_achevement, '') as timestamp)  as date_achevement,
        cast(nullif(create_date, '') as timestamp)      as create_date,
        cast(nullif(write_date, '') as timestamp)       as write_date

    from source
    where id is not null
)

select * from cleaned
