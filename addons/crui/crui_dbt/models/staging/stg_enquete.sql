-- stg_enquete.sql
-- Silver Layer: Cleans and standardizes the raw enquete (follow-up survey) table from Odoo.

with source as (
    select * from {{ source('odoo_raw', 'enquete') }}
),

cleaned as (
    select
        id                                              as enquete_id,
        projet_id,
        etat_avancement,
        observation_suivi,

        -- Actuals vs Plan tracking (used in KPI 8 & 9)
        cast(montant_investissement_reel as numeric)    as montant_investissement_reel,
        cast(nombre_emplois_reel as integer)            as nombre_emplois_reel,
        cast(pourcentage_realisation as numeric)        as pourcentage_realisation,

        -- Key survey timestamps
        cast(nullif(date_suivi_effectue, '') as timestamp)          as date_suivi_effectue,
        cast(nullif(date_autorisation, '') as timestamp)            as date_autorisation,
        cast(nullif(date_lancement_effective, '') as timestamp)     as date_lancement_effective,
        cast(nullif(date_fin_travaux, '') as timestamp)             as date_fin_travaux,
        cast(nullif(date_demarage_activite, '') as timestamp)       as date_demarage_activite,

        -- Odoo standard metadata
        cast(nullif(create_date, '') as timestamp)                  as create_date,
        cast(nullif(write_date, '') as timestamp)                   as write_date

    from source
    where id is not null
)

select * from cleaned
