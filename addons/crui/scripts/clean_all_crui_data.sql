-- =====================================================================
-- NETTOYAGE COMPLET DES TABLES DE RÉFÉRENCE CRUI - RÉGION FÈS-MEKNÈS
-- Date : 2026-08-27
-- Tables traitées : foncier, macrosecteur, act, secteur, commune
-- =====================================================================

BEGIN;

-- =====================================================================
-- 1. TABLE : foncier (Régimes Fonciers Standards au Maroc)
-- =====================================================================

-- Standardiser les noms des régimes de base
UPDATE foncier SET name = 'Melk Privé (Titre Foncier)' WHERE id = 1;
UPDATE foncier SET name = 'Domaine Privé de l''État'   WHERE id = 2;
UPDATE foncier SET name = 'Lot en Parc Industriel / ZAE' WHERE id = 3;
UPDATE foncier SET name = 'Terres Collectives (Soulaliyate)' WHERE id = 4;
UPDATE foncier SET name = 'Domaine Forestier'         WHERE id = 8;
UPDATE foncier SET name = 'Habous'                     WHERE id = 20;
UPDATE foncier SET name = 'Domaine Public / Communal' WHERE id = 21;
UPDATE foncier SET name = 'Non Immatriculé / Réquisition' WHERE id = 13;

-- Réassigner les projets vers les IDs standards
-- 1. Melk Privé / Titre Foncier -> id 1
UPDATE projet SET foncier_id = 1 WHERE foncier_id IN (5, 6, 26, 33, 34, 56, 9, 12, 19, 22, 23, 24, 27, 30, 31, 32, 35, 36, 37, 39, 42, 44, 47, 48, 50, 51, 52, 53, 54, 55);
UPDATE foncier_projet_rel SET foncier_id = 1 WHERE foncier_id IN (5, 6, 26, 33, 34, 56, 9, 12, 19, 22, 23, 24, 27, 30, 31, 32, 35, 36, 37, 39, 42, 44, 47, 48, 50, 51, 52, 53, 54, 55);

-- 2. Domaine Privé de l'État -> id 2
UPDATE projet SET foncier_id = 2 WHERE foncier_id IN (7, 18, 25);
UPDATE foncier_projet_rel SET foncier_id = 2 WHERE foncier_id IN (7, 18, 25);

-- 3. Terres Collectives -> id 4
UPDATE projet SET foncier_id = 4 WHERE foncier_id IN (11, 17, 49);
UPDATE foncier_projet_rel SET foncier_id = 4 WHERE foncier_id IN (11, 17, 49);

-- 4. Domaine Forestier -> id 8
UPDATE projet SET foncier_id = 8 WHERE foncier_id IN (43, 46);
UPDATE foncier_projet_rel SET foncier_id = 8 WHERE foncier_id IN (43, 46);

-- 5. Habous -> id 20
UPDATE projet SET foncier_id = 20 WHERE foncier_id IN (41);
UPDATE foncier_projet_rel SET foncier_id = 20 WHERE foncier_id IN (41);

-- 6. Domaine Public / Communal -> id 21
UPDATE projet SET foncier_id = 21 WHERE foncier_id IN (10, 28, 29, 45);
UPDATE foncier_projet_rel SET foncier_id = 21 WHERE foncier_id IN (10, 28, 29, 45);

-- 7. Non Immatriculé / Réquisition -> id 13
UPDATE projet SET foncier_id = 13 WHERE foncier_id IN (14, 15, 16, 38, 40);
UPDATE foncier_projet_rel SET foncier_id = 13 WHERE foncier_id IN (14, 15, 16, 38, 40);

-- Supprimer tous les doublons et numéros de TF dans foncier
DELETE FROM foncier_projet_rel WHERE foncier_id NOT IN (1, 2, 3, 4, 8, 13, 20, 21);
DELETE FROM foncier WHERE id NOT IN (1, 2, 3, 4, 8, 13, 20, 21);


-- =====================================================================
-- 2. TABLE : macrosecteur (8 Macro-Secteurs Économiques Standards)
-- =====================================================================

UPDATE macrosecteur SET name = 'Industrie & Énergie'         WHERE id = 32;
UPDATE macrosecteur SET name = 'Agro-industrie & Agriculture' WHERE id = 7;
UPDATE macrosecteur SET name = 'Tourisme, Hôtellerie & Loisirs' WHERE id = 18;
UPDATE macrosecteur SET name = 'Services, IT & Offshoring'   WHERE id = 31;
UPDATE macrosecteur SET name = 'BTP & Immobilier'            WHERE id = 19;
UPDATE macrosecteur SET name = 'Commerce & Distribution'     WHERE id = 8;
UPDATE macrosecteur SET name = 'Logistique & Transport'      WHERE id = 15;
UPDATE macrosecteur SET name = 'Santé & Enseignement'        WHERE id = 34;

-- Réassigner les tables de liaison macrosecteur_projet_rel
UPDATE macrosecteur_projet_rel SET macrosecteur_id = 32 WHERE macrosecteur_id IN (6, 12, 13, 21, 22, 26, 27, 28, 30, 33, 35);
UPDATE macrosecteur_projet_rel SET macrosecteur_id = 7  WHERE macrosecteur_id IN (23, 25);
UPDATE macrosecteur_projet_rel SET macrosecteur_id = 18 WHERE macrosecteur_id IN (5, 9, 10, 11, 14, 16);
UPDATE macrosecteur_projet_rel SET macrosecteur_id = 31 WHERE macrosecteur_id IN (24, 29);
UPDATE macrosecteur_projet_rel SET macrosecteur_id = 15 WHERE macrosecteur_id IN (17, 20);

DELETE FROM macrosecteur_projet_rel WHERE macrosecteur_id NOT IN (7, 8, 15, 18, 19, 31, 32, 34);
DELETE FROM macrosecteur WHERE id NOT IN (7, 8, 15, 18, 19, 31, 32, 34);


-- =====================================================================
-- 3. TABLE : act (Actes Administratifs & Décisions CRUI Standards)
-- =====================================================================

UPDATE act SET name = 'Accord de principe CRUI' WHERE id = 1;
UPDATE act SET name = 'Permis de construire'   WHERE id = 2;
UPDATE act SET name = 'Dérogation urbanistique' WHERE id = 3;
UPDATE act SET name = 'Attribution de lot en Zone Industrielle' WHERE id = 4;
UPDATE act SET name = 'Étude d''impact sur l''environnement' WHERE id = 6;
UPDATE act SET name = 'Autorisation d''occupation temporaire (AOT)' WHERE id = 17;
UPDATE act SET name = 'Attestation de Vocation Non Agricole (AVNA)' WHERE id = 10;
UPDATE act SET name = 'Convention d''Investissement avec l''État' WHERE id = 23;
UPDATE act SET name = 'Classement d''exploitation touristique' WHERE id = 28;
UPDATE act SET name = 'Autorisation de lotir' WHERE id = 38;

-- Réassigner les relations act_dossier_rel et act_soumission_rel
UPDATE act_dossier_rel SET act_id = 10 WHERE act_id IN (29);
UPDATE act_dossier_rel SET act_id = 2  WHERE act_id IN (5);
UPDATE act_dossier_rel SET act_id = 3  WHERE act_id IN (11, 30);
UPDATE act_dossier_rel SET act_id = 4  WHERE act_id IN (8, 9, 13, 21, 24, 32, 34, 36, 37);
UPDATE act_dossier_rel SET act_id = 28 WHERE act_id IN (7, 12, 15, 16, 20, 27);
UPDATE act_dossier_rel SET act_id = 1  WHERE act_id IN (14, 18, 19, 22, 25, 26, 31, 33, 35);

UPDATE act_soumission_rel SET act_id = 10 WHERE act_id IN (29);
UPDATE act_soumission_rel SET act_id = 2  WHERE act_id IN (5);
UPDATE act_soumission_rel SET act_id = 3  WHERE act_id IN (11, 30);
UPDATE act_soumission_rel SET act_id = 4  WHERE act_id IN (8, 9, 13, 21, 24, 32, 34, 36, 37);
UPDATE act_soumission_rel SET act_id = 28 WHERE act_id IN (7, 12, 15, 16, 20, 27);
UPDATE act_soumission_rel SET act_id = 1  WHERE act_id IN (14, 18, 19, 22, 25, 26, 31, 33, 35);

DELETE FROM act_dossier_rel WHERE act_id NOT IN (1, 2, 3, 4, 6, 10, 17, 23, 28, 38);
DELETE FROM act_soumission_rel WHERE act_id NOT IN (1, 2, 3, 4, 6, 10, 17, 23, 28, 38);
DELETE FROM act WHERE id NOT IN (1, 2, 3, 4, 6, 10, 17, 23, 28, 38);


-- =====================================================================
-- 4. TABLE : secteur (Secteurs d'activité propres)
-- =====================================================================

-- Nettoyer et standardiser les secteurs principaux
UPDATE secteur SET name = 'Agro-alimentaire & Transformation' WHERE id = 150;
UPDATE secteur SET name = 'Textile, Habillement & Cuir'     WHERE id = 183;
UPDATE secteur SET name = 'Industrie Chimique & Parachimique' WHERE id = 15;
UPDATE secteur SET name = 'Industrie Automobile & Transport' WHERE id = 187;
UPDATE secteur SET name = 'Industrie Métallurgique & Mécanique' WHERE id = 119;
UPDATE secteur SET name = 'Energies Renouvelables & Environnement' WHERE id = 16;
UPDATE secteur SET name = 'Hôtellerie, Tourisme & Restauration' WHERE id = 10;
UPDATE secteur SET name = 'Offshoring, IT & Télécoms'        WHERE id = 48;
UPDATE secteur SET name = 'BTP & Matériaux de Construction'  WHERE id = 63;
UPDATE secteur SET name = 'Santé, Médical & Pharmaceutique'  WHERE id = 19;
UPDATE secteur SET name = 'Agriculture, Élevage & Forêt'    WHERE id = 138;
UPDATE secteur SET name = 'Commerce, Distribution & Logistique' WHERE id = 88;
UPDATE secteur SET name = 'Enseignement & Formation'         WHERE id = 137;
UPDATE secteur SET name = 'Artisanat & Métiers d''Art'       WHERE id = 84;
UPDATE secteur SET name = 'Immobilier & Aménagement'        WHERE id = 23;
UPDATE secteur SET name = 'Mines & Carrières'               WHERE id = 8;

-- Réassigner les liaisons Many2Many projet_secteur_rel vers les secteurs propres
UPDATE projet_secteur_rel SET secteur_id = 150 WHERE secteur_id IN (7, 21, 62, 72, 109, 115, 130, 150, 189, 190, 192, 207, 208, 215);
UPDATE projet_secteur_rel SET secteur_id = 183 WHERE secteur_id IN (5, 11, 25, 31, 38, 39, 41, 55, 83, 123, 225);
UPDATE projet_secteur_rel SET secteur_id = 15  WHERE secteur_id IN (15, 45, 51, 217, 220);
UPDATE projet_secteur_rel SET secteur_id = 187 WHERE secteur_id IN (87, 100, 125, 173, 178, 187, 198);
UPDATE projet_secteur_rel SET secteur_id = 119 WHERE secteur_id IN (12, 64, 65, 67, 119, 121, 152, 158, 164, 206, 210, 224, 230);
UPDATE projet_secteur_rel SET secteur_id = 16  WHERE secteur_id IN (16, 46, 126, 132, 156, 159, 169, 211);
UPDATE projet_secteur_rel SET secteur_id = 10  WHERE secteur_id IN (6, 10, 18, 36, 57, 58, 77, 98, 101, 113, 118, 128, 129, 134, 143, 149, 180, 184, 188, 194, 196);
UPDATE projet_secteur_rel SET secteur_id = 48  WHERE secteur_id IN (14, 40, 48, 49, 92, 96, 97, 107, 108, 176, 182, 186, 214, 216, 228, 229);
UPDATE projet_secteur_rel SET secteur_id = 63  WHERE secteur_id IN (28, 37, 42, 43, 63, 106, 122, 172, 181);
UPDATE projet_secteur_rel SET secteur_id = 19  WHERE secteur_id IN (19, 20, 94, 102, 133, 147, 153, 154, 163, 185);
UPDATE projet_secteur_rel SET secteur_id = 138 WHERE secteur_id IN (33, 44, 50, 52, 61, 74, 124, 138, 162);
UPDATE projet_secteur_rel SET secteur_id = 88  WHERE secteur_id IN (9, 26, 30, 32, 56, 70, 71, 73, 76, 78, 80, 82, 86, 88, 99, 104, 140, 141, 148, 151, 157, 160, 171, 191, 205, 209, 223, 231);
UPDATE projet_secteur_rel SET secteur_id = 137 WHERE secteur_id IN (34, 47, 75, 137, 199);
UPDATE projet_secteur_rel SET secteur_id = 84  WHERE secteur_id IN (17, 35, 84, 85, 89, 90, 93, 117, 120, 144, 179, 227);
UPDATE projet_secteur_rel SET secteur_id = 23  WHERE secteur_id IN (22, 23, 95);
UPDATE projet_secteur_rel SET secteur_id = 8   WHERE secteur_id IN (8, 13, 24, 170, 201, 203, 218, 219);

-- Supprimer les doublons de projet_secteur_rel puis supprimer les secteurs obsolètes
DELETE FROM projet_secteur_rel WHERE secteur_id NOT IN (8, 10, 15, 16, 19, 23, 48, 63, 84, 88, 119, 137, 138, 150, 183, 187);
DELETE FROM secteur_visite_rel WHERE secteur_id NOT IN (8, 10, 15, 16, 19, 23, 48, 63, 84, 88, 119, 137, 138, 150, 183, 187);
DELETE FROM secteur WHERE id NOT IN (8, 10, 15, 16, 19, 23, 48, 63, 84, 88, 119, 137, 138, 150, 183, 187);


-- =====================================================================
-- 5. TABLE : commune (Nettoyage des paragraphes & doublons)
-- =====================================================================

-- Standardiser les principales communes de la région
UPDATE commune SET name = 'Fès - Agdal'          WHERE id = 1;
UPDATE commune SET name = 'Fès - Médina'         WHERE id = 2;
UPDATE commune SET name = 'Fès - Saïss'          WHERE id = 56;
UPDATE commune SET name = 'Fès - Zouagha'        WHERE id = 149;
UPDATE commune SET name = 'Aïn Cheggag'          WHERE id = 4;
UPDATE commune SET name = 'Aïn Chkef'            WHERE id = 70;
UPDATE commune SET name = 'Meknès'               WHERE id = 50;
UPDATE commune SET name = 'Ifrane'               WHERE id = 95;
UPDATE commune SET name = 'Azrou'                WHERE id = 90;
UPDATE commune SET name = 'Sefrou'               WHERE id = 89;
UPDATE commune SET name = 'Bhalil'               WHERE id = 28;
UPDATE commune SET name = 'Imouzzer Kandar'      WHERE id = 142;
UPDATE commune SET name = 'El Hajeb'             WHERE id = 138;
UPDATE commune SET name = 'Aït Boubidmane'       WHERE id = 40;
UPDATE commune SET name = 'Aït Bourzouine'       WHERE id = 75;
UPDATE commune SET name = 'Aït Yaâzem'           WHERE id = 57;
UPDATE commune SET name = 'Aït Sebaâ Lajrouf'    WHERE id = 235;
UPDATE commune SET name = 'Boulemane'            WHERE id = 108;
UPDATE commune SET name = 'Guigou'               WHERE id = 141;
UPDATE commune SET name = 'Missour'              WHERE id = 212;
UPDATE commune SET name = 'Moulay Yacoub'        WHERE id = 114;
UPDATE commune SET name = 'Taounate'             WHERE id = 145;
UPDATE commune SET name = 'Bouchabel'            WHERE id = 172;
UPDATE commune SET name = 'Taza'                 WHERE id = 25;
UPDATE commune SET name = 'Ghiata Al Gharbia'    WHERE id = 55;
UPDATE commune SET name = 'Bab Marzouka'         WHERE id = 182;
UPDATE commune SET name = 'Bni Frassen'          WHERE id = 53;
UPDATE commune SET name = 'Bni Lent'             WHERE id = 105;
UPDATE commune SET name = 'Oulad Zbair'          WHERE id = 131;

-- Réassigner les projets pointant vers des doublons/paragraphes de communes
UPDATE projet SET commune_id = 4   WHERE commune_id IN (125, 228);
UPDATE projet SET commune_id = 70  WHERE commune_id IN (65);
UPDATE projet SET commune_id = 40  WHERE commune_id IN (41);
UPDATE projet SET commune_id = 75  WHERE commune_id IN (74);
UPDATE projet SET commune_id = 57  WHERE commune_id IN (159);
UPDATE projet SET commune_id = 235 WHERE commune_id IN (229);
UPDATE projet SET commune_id = 1   WHERE commune_id IN (7, 9);
UPDATE projet SET commune_id = 55  WHERE commune_id IN (54, 130, 164, 206);
UPDATE projet SET commune_id = 172 WHERE commune_id IN (170);
UPDATE projet SET commune_id = 138 WHERE commune_id IN (183);
UPDATE projet SET commune_id = 182 WHERE commune_id IN (113);

-- Pour tous les autres projets dont le commune_id pointe vers une entrée bruitée, réaffecter à la commune principale de leur préfecture
UPDATE projet p
SET commune_id = CASE 
    WHEN p.prefecture_id = 135 THEN 1   -- Fès
    WHEN p.prefecture_id = 136 THEN 50  -- Meknès
    WHEN p.prefecture_id = 137 THEN 89  -- Sefrou
    WHEN p.prefecture_id = 138 THEN 95  -- Ifrane
    WHEN p.prefecture_id = 70  THEN 138 -- El Hajeb
    WHEN p.prefecture_id = 71  THEN 114 -- Moulay Yacoub
    WHEN p.prefecture_id = 84  THEN 145 -- Taounate
    WHEN p.prefecture_id = 75  THEN 108 -- Boulemane
    WHEN p.prefecture_id = 73  THEN 25  -- Taza
    ELSE 1
END
WHERE p.commune_id NOT IN (1, 2, 4, 25, 28, 40, 50, 53, 55, 56, 57, 70, 75, 89, 90, 95, 105, 108, 114, 131, 138, 141, 142, 145, 149, 172, 182, 212, 235);

-- Supprimer toutes les communes parasites
DELETE FROM commune WHERE id NOT IN (1, 2, 4, 25, 28, 40, 50, 53, 55, 56, 57, 70, 75, 89, 90, 95, 105, 108, 114, 131, 138, 141, 142, 145, 149, 172, 182, 212, 235);

COMMIT;
