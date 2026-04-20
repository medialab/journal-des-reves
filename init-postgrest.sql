-- ============================================================================
-- Configuration PostgREST pour l'API REST sans authentification
-- ============================================================================

--- web_anon : c'est un compte Postgrest, pas django : Il représente les visiteurs anonymes de ton API
-- ÉTAPE 1: Créer un rôle (utilisateur) anonyme pour PostgREST
-- ============================================================================
-- CREATE ROLE: crée un nouvel utilisateur PostgreSQL appelé "web_anon"
-- NOLOGIN: ce rôle NE PEUT PAS se connecter directement à PostgreSQL
--          (c'est juste un conteneur de permissions pour l'API)
CREATE ROLE web_anon NOLOGIN;

-- ÉTAPE 2: Donner permission de se CONNECTER à la base
-- ============================================================================
-- GRANT CONNECT: permet au rôle "web_anon" d'accéder à la base "reves_prod"
-- (sans ça, web_anon ne peut rien faire du tout)
GRANT CONNECT ON DATABASE reves_prod TO web_anon;

-- ÉTAPE 3: Donner permission sur le SCHÉMA public
-- ============================================================================
-- GRANT USAGE ON SCHEMA: permet à web_anon de "voir" les tables dans le schéma public
-- (c'est comme avoir accès au dossier où se trouvent les tables)
GRANT USAGE ON SCHEMA public TO web_anon;

-- ÉTAPE 4: Donner permission de LIRE les tables existantes
-- ============================================================================
-- GRANT SELECT: permet à web_anon de faire "SELECT" (lire) sur TOUTES les tables
-- ALL TABLES: s'applique à TOUTES les tables qui existent maintenant dans public
GRANT SELECT ON ALL TABLES IN SCHEMA public TO web_anon;

-- ÉTAPE 5: Configurer les permissions PAR DÉFAUT pour les FUTURES tables
-- ============================================================================
-- ALTER DEFAULT PRIVILEGES: configure les permissions automatiques
-- pour les NOUVELLES tables qu'on créera plus tard
-- (sinon les nouvelles tables n'auraient pas les permissions)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO web_anon;

-- ÉTAPE 6: Donner permission sur les SÉQUENCES (compteurs d'ID)
-- ============================================================================
-- GRANT USAGE ON ALL SEQUENCES: permet à web_anon d'utiliser les séquences
-- LES SÉQUENCES: ce sont les compteurs PostgreSQL qui génèrent les ID auto-incrémentés
-- (ex: id=1, id=2, id=3... automatiquement)
-- Sans ça, PostgREST ne peut pas insérer de nouvelles lignes
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO web_anon;

-- ÉTAPE 7: Configurer les permissions PAR DÉFAUT pour les FUTURES séquences
-- ============================================================================
-- Même chose que ÉTAPE 5, mais pour les futures séquences
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO web_anon;

-- ============================================================================
-- SÉCURITÉ STRICTE: Row Level Security (RLS)
-- Chaque utilisateur voit uniquement SES données (rêves + questionnaire)
-- ============================================================================

-- ÉTAPE 8: Activer RLS sur la table des rêves
-- ============================================================================
-- ALTER TABLE ... ENABLE ROW LEVEL SECURITY: active la sécurité par ligne
-- = PostgreSQL vérifiera qui fait la requête avant de retourner les données
-- (par défaut, toutes les requêtes sont rejetées jusqu'à création de policy)
ALTER TABLE reves_reve ENABLE ROW LEVEL SECURITY;

-- ÉTAPE 9: Créer une policy pour les rêves
-- ============================================================================
-- CREATE POLICY: crée une règle qui dit "tu peux voir ce rêve SI..."
-- FOR SELECT = cette rule s'applique à la lecture (SELECT)
-- TO web_anon = s'applique au rôle web_anon (l'API)
-- USING (...) = la condition: le USER_ID du rêve doit être l'utilisateur courant
--
-- EXPLICATION: 
--   reves_reve.profil_id → va chercher le profil lié
--   → reves_profil.user_id → récupère le user Django
--   current_setting('app.user_id') → récupère l'ID de l'utilisateur connecté
--   Les deux doivent être égaux pour voir le rêve
CREATE POLICY user_can_view_own_reves ON reves_reve
  FOR SELECT
  TO web_anon
  USING (
    (SELECT user_id FROM reves_profil WHERE id = reves_reve.profil_id) 
    = CAST(current_setting('app.user_id', true) AS INT)
  );

-- ÉTAPE 10: Activer RLS sur la table des questionnaires
-- ============================================================================
-- Même concept que pour les rêves
ALTER TABLE reves_questionnaire ENABLE ROW LEVEL SECURITY;

-- ÉTAPE 11: Créer une policy pour les questionnaires
-- ============================================================================
-- Same logic: tu vois uniquement TES questionnaires
CREATE POLICY user_can_view_own_questionnaire ON reves_questionnaire
  FOR SELECT
  TO web_anon
  USING (
    (SELECT user_id FROM reves_profil WHERE id = reves_questionnaire.profil_id) 
    = CAST(current_setting('app.user_id', true) AS INT)
  );

-- ============================================================================
-- COMMENT ÇA MARCHE AVEC L'API?
-- ============================================================================
-- 
-- 1. L'utilisateur envoie une requête avec JWT:
--    GET http://localhost:3000/reves_reve
--    Authorization: Bearer eyJhbGc...
--
-- 2. PostgREST décrypte le JWT et extrait l'ID utilisateur
--
-- 3. PostgREST set la variable: current_setting('app.user_id') = 42
--
-- 4. PostgreSQL exécute: SELECT * FROM reves_reve
--    Mais RLS filtre automatiquement: 
--    → Affiche que les rêves du user 42
--    → Les rêves des autres utilisateurs sont invisibles
--
-- EXEMPLE CONCRET:
--   User 1 (Alice) demande les rêves
--   → Voit uniquement ses 5 rêves
--   
--   User 2 (Bob) demande les rêves
--   → Voit uniquement ses 3 rêves
--   
--   User 1 + User 2 ensemble = 8 rêves en BD
--   → Mais chacun voit que les siens (5 et 3)
--   → Impossible de voir les données de l'autre!

