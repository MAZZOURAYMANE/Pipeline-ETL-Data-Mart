-- dim_project.sql
-- Gold Layer: Dimension table enriching project records with location and partner attributes.

with projet as (
    select * from {{ ref('stg_projet') }}
),

prefecture as (
    select id as prefecture_id, name as prefecture_name
    from {{ source('odoo_raw', 'prefecture') }}
),

commune as (
    select id as commune_id, name as commune_name
    from {{ source('odoo_raw', 'commune') }}
),

partner as (
    select id as partner_id, name as partner_name
    from {{ source('odoo_raw', 'res_partner') }}
),

foncier as (
    select id as foncier_id, name as foncier_type
    from {{ source('odoo_raw', 'foncier') }}
),

final as (
    select
        -- Surrogate key
        p.projet_id,

        -- Project identifiers
        p.identifiant_projet,
        p.reference,
        p.projet_name,
        p.statut_projet,
        p.raison_social,
        p.forme_juridique,
        p.consistance,
        p.composante,
        p.surface,
        p.reference_fonciere,
        p.dispositions_urbanistiques,
        p.annee,

        -- Plan financials
        p.montant_investissement,
        p.nombre_emploi,
        p.duree_projet_days,

        -- Location attributes (denormalized for OLAP)
        pre.prefecture_name,
        com.commune_name,
        fon.foncier_type,

        -- Petitionnaire
        par.partner_name              as petitionnaire_name,

        -- Project timeline
        p.date_lancement,
        p.date_achevement,

        -- CDC metadata
        p.create_date,
        p.write_date

    from projet p
    left join prefecture pre using (prefecture_id)
    left join commune com using (commune_id)
    left join partner par using (partner_id)
    left join foncier fon using (foncier_id)
)

select * from final
