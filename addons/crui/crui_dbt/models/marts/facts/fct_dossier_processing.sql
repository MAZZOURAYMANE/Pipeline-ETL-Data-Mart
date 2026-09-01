-- fct_dossier_processing.sql
-- Gold Layer: Core fact table capturing every dossier's processing lifecycle and SLA metrics.

with dossier as (
    select * from {{ ref('stg_dossier') }}
),

projet as (
    select projet_id, projet_name, annee, prefecture_id, commune_id
    from {{ ref('stg_projet') }}
),

date_dim as (
    select date_key, day_date from {{ ref('dim_date') }}
),

final as (
    select
        -- Surrogate / Natural Keys
        d.dossier_id,
        d.projet_id,
        d.reference                              as dossier_reference,
        d.dossier_name,
        d.statut_dossier,
        d.etat_procedure,
        d.annee,

        -- Decisions
        d.decision_crui,
        d.decision_dossier,
        d.avis_wali,
        d.avis_recours_ministeriel,
        d.etat_decision_wali,
        d.decision_comite_ministeriel,
        d.recours_wali,
        d.recours_comite_ministeriel,
        d.argument_crui,

        -- SLA Boolean Flags
        d.is_submitted_within_30j,
        d.is_examined_within_30j,
        d.is_approved_crui,

        -- Computed Duration Measures (all in working days)
        d.delai_traitement_working_days,
        d.delai_examen_crui_working_days,
        d.delai_delivrance_act_working_days,
        d.delai_total_working_days,
        d.delai_instruction_crui_working_days,

        -- Process Timestamp Keys (FK to dim_date)
        to_char(d.date_depot, 'YYYYMMDD')::int       as date_depot_key,
        to_char(d.date_diffusion, 'YYYYMMDD')::int   as date_diffusion_key,
        to_char(d.date_passage, 'YYYYMMDD')::int     as date_passage_key,
        to_char(d.date_delivrance, 'YYYYMMDD')::int  as date_delivrance_key,

        -- Raw timestamps (for detailed queries)
        d.date_depot,
        d.date_retour_spoc,
        d.date_diffusion,
        d.date_passage,
        d.date_delivrance,
        d.date_leve_reserve,
        d.date_insertion,

        -- Project context
        p.projet_name,

        -- CDC metadata
        d.create_date,
        d.write_date

    from dossier d
    left join projet p using (projet_id)
)

select * from final
