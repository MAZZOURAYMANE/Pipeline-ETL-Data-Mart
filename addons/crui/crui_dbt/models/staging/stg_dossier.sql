-- stg_dossier.sql
-- Silver Layer: Cleans and standardizes the raw dossier table from Odoo.

with source as (
    select * from {{ source('odoo_raw', 'dossier') }}
),

cleaned as (
    select
        id                                          as dossier_id,
        projet_id,
        reference,
        name                                        as dossier_name,
        statut_dossier,
        etat_procedure,
        annee,

        -- Decision fields
        decision_crui,
        decision_dossier,
        argument_crui,
        avis_wali,
        avis_recours_ministeriel,
        etat_decision_wali,
        decision_comite_ministeriel,
        recours_wali,
        recours_comite_ministeriel,

        -- Computed KPI fields (pre-computed by Odoo, stored=True)
        cast(delai_moyen_traitement as integer)     as delai_traitement_working_days,
        cast(delai_examen_crui as integer)          as delai_examen_crui_working_days,
        cast(delai_delivrance_act as integer)       as delai_delivrance_act_working_days,
        cast(delai_total_traitement_dossier as integer) as delai_total_working_days,
        cast(delai_instruction_crui as integer)     as delai_instruction_crui_working_days,

        -- Boolean SLA flags
        cast(soumis_30j as boolean)                 as is_submitted_within_30j,
        cast(examine_30j as boolean)                as is_examined_within_30j,
        cast(approuve_crui as boolean)              as is_approved_crui,

        -- Key process timestamps
        cast(nullif(date_depot, '') as timestamp)                     as date_depot,
        cast(nullif(date_retour_spoc, '') as timestamp)               as date_retour_spoc,
        cast(nullif(date_diffusion, '') as timestamp)                 as date_diffusion,
        cast(nullif(date_passage, '') as timestamp)                   as date_passage,
        cast(nullif(date_delivrance, '') as timestamp)                as date_delivrance,
        cast(nullif(date_insertion, '') as timestamp)                 as date_insertion,
        cast(nullif(date_leve_reserve, '') as timestamp)              as date_leve_reserve,
        cast(nullif(date_depot_lettre_recours, '') as timestamp)      as date_depot_lettre_recours,
        cast(nullif(date_comite_ministeriel, '') as timestamp)        as date_comite_ministeriel,

        -- Odoo standard metadata
        cast(nullif(create_date, '') as timestamp)                    as create_date,
        cast(nullif(write_date, '') as timestamp)                     as write_date

    from source
    where id is not null
)

select * from cleaned
