-- fct_project_followup.sql
-- Gold Layer: Fact table capturing project follow-up surveys (enquêtes) 
-- tracking real vs. planned investment and employment KPIs.

with enquete as (
    select * from {{ ref('stg_enquete') }}
),

projet as (
    select
        projet_id,
        projet_name,
        montant_investissement          as montant_investissement_prevu,
        nombre_emploi                   as nombre_emploi_prevu,
        annee
    from {{ ref('stg_projet') }}
),

final as (
    select
        -- Natural Keys
        e.enquete_id,
        e.projet_id,

        -- Survey attributes
        e.etat_avancement,
        e.observation_suivi,

        -- Actual KPI Measures
        e.montant_investissement_reel,
        e.nombre_emplois_reel,
        e.pourcentage_realisation,

        -- Planned KPI context (denormalized from project)
        p.montant_investissement_prevu,
        p.nombre_emploi_prevu,
        p.annee,
        p.projet_name,

        -- Derived KPI Measures
        case
            when p.montant_investissement_prevu > 0
            then round(
                (e.montant_investissement_reel / p.montant_investissement_prevu) * 100, 2
            )
            else 0
        end                             as pct_investissement_realise,

        case
            when p.nombre_emploi_prevu > 0
            then round(
                (e.nombre_emplois_reel::numeric / p.nombre_emploi_prevu) * 100, 2
            )
            else 0
        end                             as pct_emplois_realises,

        -- Date Keys (FK to dim_date)
        to_char(e.date_suivi_effectue, 'YYYYMMDD')::int   as date_suivi_key,
        to_char(e.date_autorisation, 'YYYYMMDD')::int     as date_autorisation_key,
        to_char(e.date_fin_travaux, 'YYYYMMDD')::int      as date_fin_travaux_key,

        -- Raw timestamps
        e.date_suivi_effectue,
        e.date_autorisation,
        e.date_lancement_effective,
        e.date_fin_travaux,
        e.date_demarage_activite,

        -- CDC metadata
        e.create_date,
        e.write_date

    from enquete e
    left join projet p using (projet_id)
)

select * from final
