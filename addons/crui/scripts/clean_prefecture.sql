-- ============================================================
-- NETTOYAGE TABLE prefecture - Région Fès-Meknès
-- Date : 2026-08-27
-- Objectif : Garder uniquement les 7 Préfectures/Provinces
--            officielles de la région et supprimer tous doublons
-- ============================================================

BEGIN;

-- ============================================================
-- ETAPE 1 : Créer des entrées propres pour les 7 entités officielles
-- ============================================================

-- On utilise les IDs existants qui ont des projets liés
-- ou on crée des nouvelles entrées standardisées.

-- Noms officiels finaux choisis :
--   135 → Préfecture de Fès
--   136 → Préfecture de Meknès
--   137 → Province de Sefrou
--   138 → Province d'Ifrane
--   + 3 nouvelles : El Hajeb, Moulay Yacoub, Taounate, Boulemane, Taza

-- Mettre à jour les noms des entrées qui ont des projets attachés
UPDATE prefecture SET name = 'Préfecture de Fès'    WHERE id = 135;
UPDATE prefecture SET name = 'Préfecture de Meknès' WHERE id = 136;
UPDATE prefecture SET name = 'Province de Sefrou'   WHERE id = 137;
UPDATE prefecture SET name = "Province d'Ifrane"    WHERE id = 138;

-- Créer les 5 provinces manquantes avec des noms propres
-- (El Hajeb, Moulay Yacoub, Taounate, Boulemane, Taza)
-- On va réutiliser les IDs les plus anciens pour chaque groupe.

-- El Hajeb : garder id=70, renommer proprement
UPDATE prefecture SET name = 'Province d''El Hajeb' WHERE id = 70;

-- Moulay Yacoub : garder id=71
UPDATE prefecture SET name = 'Province de Moulay Yacoub' WHERE id = 71;

-- Taounate : garder id=84
UPDATE prefecture SET name = 'Province de Taounate' WHERE id = 84;

-- Boulemane : garder id=75
UPDATE prefecture SET name = 'Province de Boulemane' WHERE id = 75;

-- Taza : garder id=73
UPDATE prefecture SET name = 'Province de Taza' WHERE id = 73;

-- ============================================================
-- ETAPE 2 : Réaffecter les projets qui pointent vers des doublons
-- ============================================================

-- Tous les variants de "Fès" → 135
UPDATE projet SET prefecture_id = 135
WHERE prefecture_id IN (
  69, 72, 85, 88, 89, 90, 92, 119, 125,   -- Fès, FES, Fsè, Fèq, Fèqs, f7S, feq, F-s
  77, 78                                    -- Fès/Sefrou, Fès/Sidi Hrazem
);

-- Tous les variants de "Meknès" → 136
UPDATE projet SET prefecture_id = 136
WHERE prefecture_id IN (
  80, 86, 94, 115, 122,                    -- Meknès, MEKNES, Mekns
  93, 116, 130                             -- MEKNES AL KIFANE, MEKNES ROMMANE, MEKNES ZARHOUN
);

-- Tous les variants de "Sefrou" → 137
UPDATE projet SET prefecture_id = 137
WHERE prefecture_id IN (
  68, 82, 83, 91, 96, 99, 112,            -- Sefrou, Sferou, Sefroun, Sefru, Serou, SEFROU
  105, 109, 131                            -- SEFROU AHMED, SEFROU AQORAR, SEFROU LAJROUF
);

-- Tous les variants de "Ifrane" → 138
UPDATE projet SET prefecture_id = 138
WHERE prefecture_id IN (
  76, 87, 104, 114                         -- Ifrane, IFRANE
);

-- Tous les variants de "El Hajeb" → 70
UPDATE projet SET prefecture_id = 70
WHERE prefecture_id IN (81, 103);          -- El Hajeb, EL HAJEB

-- Tous les variants de "Moulay Yacoub" → 71
UPDATE projet SET prefecture_id = 71
WHERE prefecture_id IN (74, 101, 111);    -- Moulay Yacoub, MOULAY YACOUB, MOULAY YAACOUB

-- Tous les variants de "Taounate" → 84
UPDATE projet SET prefecture_id = 84
WHERE prefecture_id IN (100, 123, 128);   -- TAOUNATE, Taounatz, TAOUNATE ABDELKRIM

-- Tous les variants de "Boulemane" → 75
UPDATE projet SET prefecture_id = 75
WHERE prefecture_id IN (102);             -- BOULEMANE

-- Tous les variants de "Taza" → 73
UPDATE projet SET prefecture_id = 73
WHERE prefecture_id IN (79, 98, 107, 121);  -- Taza, TAZA, TAZA GHARBIA, TAZA ACHARQIA

-- ============================================================
-- ETAPE 3 : Supprimer tous les doublons et entrées erronées
-- ============================================================

DELETE FROM prefecture WHERE id IN (
  -- Variants Fès
  69, 72, 85, 88, 89, 90, 92, 119, 125, 77, 78,
  -- Variants Meknès
  80, 86, 94, 115, 122, 93, 116, 130,
  -- Variants Sefrou
  68, 82, 83, 91, 96, 99, 112, 105, 109, 131,
  -- Variants Ifrane
  76, 87, 104, 114,
  -- Variants El Hajeb
  81, 103,
  -- Variants Moulay Yacoub
  74, 101, 111,
  -- Variants Taounate
  100, 123, 128,
  -- Variants Boulemane
  102,
  -- Variants Taza
  79, 98, 107, 121,
  -- Entrées invalides / hors région
  97,   -- Azrou (commune, pas préfecture)
  95,   -- cin cheggag (faute de frappe)
  120,  -- AIN CHEGGAG (commune)
  113,  -- AIN CHKEF (commune)
  118,  -- AGHBALOU AQORAR (commune)
  108,  -- GHIATA AL GHARBIA (commune)
  117,  -- OULAD ZBAIR (commune)
  106,  -- SIDI SLIMANE MOUL AL KIFANE (commune)
  110,  -- SIDI YOUSSEF BEN AHMED (commune)
  132,  -- MAGHRAOUA (commune)
  126,  -- 39953 (invalide)
  127,  -- MISSOUR (hors région)
  129,  -- 11382 m² (invalide)
  133,  -- N/A
  134,  -- NADOR (hors région)
  124   -- URL (invalide)
);

-- ============================================================
-- ETAPE 4 : Vérification finale
-- ============================================================

SELECT id, name FROM prefecture ORDER BY name;

COMMIT;
