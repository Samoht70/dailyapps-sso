---
description: "Task list for feature implementation"
---

# Tasks: Authentification centralisée (SSO) de l'écosystème DailyApps

**Input**: Design documents from `/specs/001-sso-central-authentication/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: incluses. `global:test-new-features` les exige et D13 les cadre — PHPUnit 12.5, un seul
lanceur, les écrans Livewire dans la même suite via `Livewire::test(...)`.

**Organization**: les tâches sont groupées par user story, chacune livrable et testable seule.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallélisable — fichiers différents, aucune dépendance sur une tâche encore ouverte
- **[Story]**: US1 à US5, les histoires de [spec.md](./spec.md)
- Chaque description porte son chemin exact

## Path Conventions

**Un seul dépôt est touché : `api`.** Tout chemin commence par `api/` — il n'y a pas de dépôt par
défaut dans un workspace. `mobile/` n'est pas concerné (research.md D14) : **aucun commit ne doit y
atterrir**, alors que `speckit.multirepo.branch` le branche par défaut.

Pas de `app/` ni de `config/` ni de `database/` à la racine de `api` — `osdd:start` les a supprimés.
Tout vit dans une couche OSDD sous `api/functional/` ou `api/technical/`. Toutes les commandes
passent par `./vendor/bin/sail`, jamais sur l'hôte.

**Le cadre est posé** : la constitution v1.0.0 est ratifiée dans `.specify/memory/constitution.md`
et la porte `Constitution Check` de [plan.md](./plan.md) est instruite contre ses six principes.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: dépendances, squelettes des six couches, et le point ouvert n°2 du plan levé avant tout

- [X] T001 Ajouter `laravel/passport` ^13.8, `jeremy379/laravel-openid-connect` ^3.3 et `livewire/livewire` ^4.4 à la section `require` de `api/composer.json`, puis `./vendor/bin/sail composer update`
- [X] T002 [P] Créer la couche `api/functional/organizations/` (composer.json `type: layer`, PSR-4 `Functional\Organizations\`, `src/Providers/OrganizationsServiceProvider.php` étendant `LayerServiceProvider`), sur le modèle de `api/functional/users/`
- [X] T003 [P] Créer la couche `api/functional/catalog/` (PSR-4 `Functional\Catalog\`, `src/Providers/CatalogServiceProvider.php`)
- [X] T004 [P] Créer la couche `api/functional/licensing/` (PSR-4 `Functional\Licensing\`, `src/Providers/LicensingServiceProvider.php`)
- [X] T005 [P] Créer la couche `api/technical/oidc/` (PSR-4 `Technical\Oidc\`, `src/Providers/OidcServiceProvider.php`)
- [X] T006 [P] Créer la couche `api/technical/audit/` (PSR-4 `Technical\Audit\`, `src/Providers/AuditServiceProvider.php`)
- [X] T007 Déclarer les cinq nouvelles couches dans `require` de `api/composer.json` (`functional/organizations`, `functional/catalog`, `functional/licensing`, `technical/oidc`, `technical/audit`, toutes en `*`)
- [X] T008 Installer Passport : `sail artisan install:api --passport` ou publication des migrations, puis `sail artisan passport:keys`, la configuration atterrissant dans `api/technical/oidc/config/passport.php` et `api/technical/oidc/config/openid.php` chargées par `OidcServiceProvider::register()` via `mergeConfigFrom()` — il n'y a pas de `config/` à la racine
- [X] T009 **Spike bloquant** — éprouver le point ouvert n°2 du plan : une vue Blade et un composant Livewire servis depuis une couche OSDD. Câbler `loadViewsFrom(__DIR__.'/../../resources/views', 'oidc')` et `Livewire::component(...)` dans `api/technical/oidc/src/Providers/OidcServiceProvider.php`, rendre une vue témoin `api/technical/oidc/resources/views/ping.blade.php` et la couvrir par un test dans `api/technical/oidc/tests/Feature/LayerViewsTest.php`. La documentation de `xefi/laravel-osdd` ne couvre ni vues ni Livewire : si cela ne fonctionne pas, arrêter et arbitrer avant la suite
- [X] T010 Faire scanner les Blade des couches par Tailwind 4 : ajouter les directives `@source '../../technical/*/resources/views'` et `@source '../../functional/*/resources/views'` dans `api/resources/css/app.css`, et charger le bundle par `@vite(['resources/css/app.css', 'resources/js/app.js'])` depuis le layout d'écran de la couche. Sans cela, les classes utilisées dans `api/technical/oidc/resources/views/` sont purgées au `npm run build` et les cinq écrans sortent sans style
- [X] T011 Lancer `sail artisan osdd:phpunit` et vérifier que `api/phpunit.xml` porte une testsuite par couche

**Checkpoint**: les six couches se chargent, une vue Livewire est servie depuis une couche.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: le modèle de données complet et le socle OIDC. Pour ce produit, le socle **est** la
relation organisation × licence × siège × accès : aucune histoire n'est démontrable sans elle.

**⚠️ CRITICAL**: aucune user story ne peut démarrer avant la fin de cette phase.

### Couche `functional/organizations`

- [X] T012 [P] Enums `OrganizationKind` (`operator` | `client`) et `OrganizationStatus` (`active` | `suspended`, défaut `active`) dans `api/functional/organizations/src/Enums/` — enums PHP, jamais de colonne `ENUM` MySQL
- [X] T013 Migration `create_organizations_table` dans `api/functional/organizations/database/migrations/` : `id` UUID, `name` string(160) requis unique, `kind`, `status` défaut `active`, `suspended_at` datetime nullable renseigné en même temps que `status = suspended`, `timestamps`, plus un index unique partiel garantissant **exactement une ligne `operator`**
- [X] T014 Modèle `Organization` dans `api/functional/organizations/src/Models/Organization.php` : casts des deux enums, relations `users` (1-n) et `licenses` (1-n)
- [X] T015 [P] `OrganizationFactory` dans `api/functional/organizations/database/factories/` avec les états `operator`, `client`, `suspended` — via le helper `faker()` de `xefi/faker-php-laravel`, jamais `fakerphp/faker`
- [X] T016 Garde de transition du statut dans `api/functional/organizations/src/Models/Concerns/` : seules `active → suspended` et `suspended → active` sont permises, et une organisation `operator` **ne peut pas** être suspendue — cela couperait l'administration de la plateforme. Transition illégale → exception métier dédiée dans `api/functional/organizations/src/Exceptions/`

### Couche `functional/users` *(existante, étendue)*

- [X] T017 [P] Enums `UserStatus` (`invited` | `active` | `disabled`, défaut `invited`) et `OrganizationRole` (`member` | `admin`) dans `api/functional/users/src/Enums/`
- [X] T018 Reprendre `api/functional/users/database/migrations/2026_09_16_195116_create_users_table.php` — rien n'est déployé et la spec exclut toute reprise de comptes, donc on modifie la migration d'origine plutôt que d'en empiler une : `id` en UUID, `organization_id` FK Organization **requis** (FR-025), `name` string(160) requis, `email` string(255) requis **unique globalement** (FR-026), `password` nullable tant que l'invitation n'est pas acceptée, `status`, `organization_role`, `disabled_at` datetime nullable, `last_authenticated_at` datetime nullable. Aucun `onDelete('cascade')`
- [X] T019 Patron State du compte dans `api/functional/users/src/States/` (D9) : classe abstraite `UserState` et `InvitedState`, `ActiveState`, `DisabledState`. Comportements portés par l'état — `canAuthenticate()` (`active` seul), `appearsInAccesses()` (`active` seul), `consumesSeat()` (`invited` **et** `active`, un siège étant réservé dès l'invitation sinon FR-024 se contourne en invitant en masse). Transitions : `invited → active`, `active → disabled`, `disabled → active` ; `disabled → invited` **toujours refusée**, exception à la clé
- [X] T020 Étendre `api/functional/users/src/Models/User.php` : casts `status` et `organization_role`, `#[Fillable]` mis à jour, relations `organization` (n-1), `applicationAccesses` (1-n), `ssoSessions` (1-n), résolution de l'état courant vers la classe de T019. Pas de table de rattachement — le rattachement unique tient en deux colonnes
- [X] T021 [P] Étendre `api/functional/users/database/factories/UserFactory.php` avec les états `invited`, `active`, `disabled`, `admin`

### Couche `functional/catalog`

- [X] T022 [P] Enum `ApplicationStatus` (`draft` | `published` | `retired`, défaut `draft`) dans `api/functional/catalog/src/Enums/`
- [X] T023 Migrations dans `api/functional/catalog/database/migrations/` : `create_applications_table` (`id` UUID, `slug` string(64) requis unique kebab-case — l'identifiant stable porté dans les claims, `name` string(160) requis, `description` text nullable, `logo_url` string nullable, `home_url` string requis, `backchannel_logout_url` string nullable, `status` défaut `draft`, `oauth_client_id` FK `oauth_clients`, `timestamps`) et `create_application_roles_table` (`id` UUID, `application_id` FK, `key` string(64) kebab-case **unique par application**, `label` string(160) requis, `description` text nullable, `timestamps`). **Aucune colonne d'adresses de retour** : elles vivent dans `oauth_clients.redirect_uris`, qui est ce qui les applique réellement
- [X] T024 Modèles `Application` et `ApplicationRole` dans `api/functional/catalog/src/Models/` : relations `roles`, `application`, `oauthClient`, casts
- [X] T025 [P] `ApplicationFactory` (états `draft`, `published`, `retired`) et `ApplicationRoleFactory` dans `api/functional/catalog/database/factories/`

### Couche `functional/licensing`

- [X] T026 Migrations dans `api/functional/licensing/database/migrations/` : `create_licenses_table` (`id` UUID, `organization_id` FK, `application_id` FK, `starts_on` date requis, `ends_on` date nullable — nul = sans échéance, `seats` unsigned int requis **≥ 1**, `timestamps`, unicité `(organization_id, application_id)` — un renouvellement déplace `ends_on`, il ne crée pas une seconde licence) ; `create_application_accesses_table` (`id` UUID, `user_id` FK, `application_id` FK, `granted_by_id` FK User nullable, `granted_at` datetime, `timestamps`, unicité `(user_id, application_id)`) ; `create_application_access_role_table` (pivot `application_access_id` × `application_role_id`, unique)
- [X] T027 Modèles `License` et `ApplicationAccess` dans `api/functional/licensing/src/Models/`, avec le pivot des rôles attribués
- [X] T028 **L'expression unique de validité d'une licence** dans `api/functional/licensing/src/Models/Concerns/` : `starts_on ≤ aujourd'hui` **et** (`ends_on` nul **ou** `≥ aujourd'hui`) **et** organisation `active` **et** application `published`. C'est cette expression, et elle seule, qui décide de FR-019 et FR-023 — aucune autre ne doit la réécrire
- [X] T029 [P] `LicenseFactory` (états `valid`, `expired`, `perpetual`, `exhausted`) et `ApplicationAccessFactory` dans `api/functional/licensing/database/factories/`

### Couche `technical/audit`

- [X] T030 [P] Enum `SecurityEventType` dans `api/technical/audit/src/Enums/` avec les dix-neuf valeurs de FR-037 : `authentication_succeeded`, `authentication_failed`, `authentication_throttled`, `session_ended`, `password_changed`, `password_reset_requested`, `invitation_sent`, `invitation_accepted`, `access_granted`, `access_revoked`, `user_disabled`, `user_enabled`, `organization_suspended`, `license_attached`, `license_revoked`, `application_published`, `application_retired`, `client_secret_rotated`, `logout_push_failed`
- [X] T031 Migration `create_security_events_table` dans `api/technical/audit/database/migrations/` : `id` UUID, `type`, `actor_id` FK User nullable (nul quand l'auteur n'est pas identifié — un échec d'identification), `organization_id` FK Organization nullable portant le périmètre de lecture de FR-038, `subject_type`/`subject_id` morph nullable, `ip_address` nullable, `user_agent` nullable, `payload` json, **`created_at` seul — pas de `updated_at`**, un événement ne se modifie pas
- [X] T032 Modèle `SecurityEvent` dans `api/technical/audit/src/Models/SecurityEvent.php` : `Prunable` réglé sur douze mois (FR-039), purge **par lots et jamais en masse**
- [X] T033 Point d'enregistrement unique des événements dans `api/technical/audit/src/Actions/RecordSecurityEvent.php`, appelé par toutes les couches, plus `SecurityEventFactory` dans `api/technical/audit/database/factories/`

### Couche `technical/oidc` — socle

- [X] T034 Configurer Passport dans `api/technical/oidc/config/passport.php` : `access_token` 15 min, `refresh_token` 8 h glissantes avec rotation, PKCE `S256` obligatoire pour tous les clients y compris confidentiels, grants `password`, `implicit` et `device` **désactivés** — seuls *authorization code* + PKCE et *client credentials* restent ouverts
- [X] T035 Modèle `Client` étendant celui de Passport dans `api/technical/oidc/src/Models/Client.php` : `skipsAuthorization()` renvoie vrai pour un client *first-party* (D5), secret haché montré une seule fois (D12). Le déclarer auprès de Passport dans `OidcServiceProvider`
- [X] T036 Migrations dans `api/technical/oidc/database/migrations/` : `create_sso_sessions_table` (`id` UUID — **c'est le claim `sid`**, `user_id` FK, `laravel_session_id` string nullable, `ip_address` nullable, `user_agent` nullable, `started_at`, `last_seen_at` alimentant l'expiration par inactivité, `expires_at` expiration absolue, `revoked_at` nullable) et `create_sso_session_participants_table` (`sso_session_id` × `application_id` unique, `first_seen_at`, `logout_pushed_at` nullable)
- [X] T037 Modèles `SsoSession` et `SsoSessionParticipant` dans `api/technical/oidc/src/Models/`, avec leurs factories dans `api/technical/oidc/database/factories/`
- [X] T038 Contrat de fournisseur de claims — le point d'extension de la couche — dans `api/technical/oidc/src/Contracts/ClaimsProvider.php`, plus son registre dans `OidcServiceProvider`. La dépendance va du fonctionnel vers le technique, jamais l'inverse : `technical/oidc` ne connaît ni licence ni accès
- [X] T039 Câbler `api/technical/oidc/src/Providers/OidcServiceProvider.php` : chargement des migrations, des vues, des traductions, des routes `web` de la couche et enregistrement des composants Livewire (reprend le spike T009)

### Permissions et amorçage

- [X] T040 Déclarer les permissions spatie de l'api dans `api/technical/permissions/database/seeders/` : déclarer/suspendre une organisation, attribuer une licence, inviter un utilisateur, attribuer un accès, déclarer/publier/retirer une application, faire tourner un secret, lire les événements de sécurité. **Vérification par permission, jamais par nom de rôle** — ces permissions gouvernent l'api du point central et n'ont rien à voir avec les `ApplicationRole` du catalogue (D6)
- [X] T041 Seeder d'amorçage dans `api/functional/organizations/database/seeders/` : l'organisation `operator` DailyApps et son compte d'administration, sans quoi le système ne peut pas démarrer
- [X] T042 Seeder de démonstration correspondant à [quickstart.md](./quickstart.md) dans `api/functional/licensing/database/seeders/` : organisations `Acme` et `Globex` ; applications publiées `leaves` et `expenses` exposant chacune les rôles `user` et `manager` ; licence `Acme × leaves` à **2 sièges** ; licence `Acme × expenses` **expirée** ; deux utilisateurs Acme, l'un avec accès à `leaves`, l'autre sans aucun accès
- [X] T043 Relancer `sail artisan osdd:phpunit` et vérifier `api/phpunit.xml`, puis `sail test` — la suite passe sur le socle

**Checkpoint**: le modèle est en base, Passport émet des jetons, le socle est prêt. Les histoires
peuvent démarrer.

---

## Phase 3: User Story 1 - Se connecter une seule fois, depuis n'importe quelle application (Priority: P1) 🎯 MVP

**Goal**: un écran de connexion unique, une session centrale, et un retour exact sur la page visée.
Une seconde application n'en redemande pas.

**Independent Test**: avec une seule application raccordée et un seul compte — un accès non identifié
aboutit à `/login`, l'identification renvoie sur la page visée, une seconde application raccordée ne
redemande rien.

### Tests for User Story 1

- [X] T044 [P] [US1] Feature test du parcours complet dans `api/technical/oidc/tests/Feature/AuthorizationCodeFlowTest.php` : `/oauth/authorize` sans session → `/login` → identification → retour **sur l'URL visée** via `intended`, puis seconde application sans nouvelle saisie
- [X] T045 [P] [US1] Feature test des refus dans `api/technical/oidc/tests/Feature/AuthorizationRefusalTest.php` : `redirect_uri` non déclarée **rejetée sans aucune redirection**, `access_denied` avec les motifs `account_unavailable`, `no_license`, `no_access`, `throttled`
- [X] T046 [P] [US1] Livewire test de l'écran de connexion dans `api/technical/oidc/tests/Feature/LoginScreenTest.php` : **message identique** que le compte existe ou non, message distinct pour compte `disabled` et organisation `suspended`, verrouillage après tentatives répétées
- [X] T047 [P] [US1] Feature test du mot de passe oublié dans `api/technical/oidc/tests/Feature/PasswordResetTest.php` : réponse **toujours identique** adresse connue ou non, lien à usage unique, lien expiré refusé, demande plus récente invalidant la précédente, mot de passe trop faible refusé **avec son motif**
- [X] T048 [P] [US1] Unit test des transitions du compte dans `api/functional/users/tests/Unit/UserStateTest.php` : `disabled → invited` refusée, `canAuthenticate()` vrai pour `active` seul, `consumesSeat()` vrai pour `invited` et `active`

### Implementation for User Story 1

- [X] T049 [US1] Composant Livewire `Login` dans `api/technical/oidc/src/Livewire/Login.php` et sa vue `api/technical/oidc/resources/views/livewire/login.blade.php` — le balisage vit en Blade, jamais concaténé dans une classe
- [X] T050 [US1] Routes `GET /login` et la soumission dans `api/technical/oidc/routes/web.php`, plus le layout d'écran dans `api/technical/oidc/resources/views/layouts/`
- [X] T051 [US1] Fichiers de traduction des cinq écrans dans `api/technical/oidc/lang/fr/` et `api/technical/oidc/lang/en/` — aucun texte utilisateur en dur
- [X] T052 [US1] Messages d'échec dans `api/technical/oidc/src/Livewire/Login.php` : **identique** que le compte existe ou non (FR-007), mais distinct pour un compte `disabled` ou une organisation `suspended` — l'utilisateur doit savoir qu'il s'agit d'un compte coupé, pas d'une faute de frappe
- [X] T053 [US1] Limitation des tentatives par compte **et** par origine dans `api/technical/oidc/src/Actions/ThrottleAuthentication.php` (FR-008), chaque blocage journalisé en `authentication_throttled`
- [X] T054 [US1] Ouverture d'une `SsoSession` à l'identification réussie dans `api/technical/oidc/src/Listeners/OpenSsoSession.php` : son `id` devient le `sid`, `last_authenticated_at` du compte est alimenté. Listener déclaré dans le service provider de couche, **jamais un observer**
- [X] T055 [US1] Expiration de session par inactivité (`last_seen_at`) **et** absolue (`expires_at`), toutes deux configurables dans `api/technical/oidc/config/`, appliquées par un middleware dans `api/technical/oidc/src/Http/Middleware/`
- [X] T056 [US1] Protéger `/oauth/authorize` par le middleware `auth` et rediriger vers `route('login')` par le mécanisme standard de Laravel dans `api/technical/oidc/src/Providers/OidcServiceProvider.php` et `api/technical/oidc/routes/web.php`, l'URL visée conservée dans la session (`intended`). **L'URL de retour n'est jamais reconstruite ni transportée dans un paramètre** — c'est ce qui la rend indétournable
- [X] T057 [US1] Rejet d'une `redirect_uri` absente de `oauth_clients.redirect_uris` : erreur affichée sur le point central, **aucune redirection** vers l'adresse fournie (FR-006), dans `api/technical/oidc/src/Http/Controllers/`
- [X] T058 [US1] Consentement ignoré pour les clients *first-party* via le `skipsAuthorization()` de T035, câblé dans `api/technical/oidc/src/Providers/OidcServiceProvider.php`
- [X] T059 [US1] Refus motivés à l'autorisation dans `api/technical/oidc/src/Actions/AuthorizeUser.php` : `account_unavailable` (compte `disabled` ou organisation `suspended`), `no_license` (aucune licence valide), `no_access` (licence valide mais aucun accès attribué) — trois réponses distinctes, FR-018 en dépend
- [X] T060 [US1] Composant Livewire `ForgotPassword` + vue + route `POST /password/forgot` dans `api/technical/oidc/src/Livewire/ForgotPassword.php` : la réponse est **toujours la même**, adresse connue ou non, sinon l'écran devient un oracle d'existence de compte
- [X] T061 [US1] Composant Livewire `ResetPassword` + vue + routes `GET /password/reset/{token}` et `POST /password/reset` dans `api/technical/oidc/src/Livewire/ResetPassword.php`, adossé à la table `password_reset_tokens` déjà présente dans `technical/framework` — haché, usage unique, durée limitée, une demande plus récente invalidant la précédente
- [X] T062 [US1] Notification de réinitialisation dans `api/functional/users/src/Notifications/PasswordResetRequested.php` — mail via notification, jamais un Mailable direct
- [X] T063 [US1] Règle de robustesse du mot de passe dans `api/functional/users/src/Rules/PasswordStrength.php`, refus **accompagné de son motif** (FR-009)
- [X] T064 [US1] Listener `CloseSessionsOnPasswordChange` dans `api/functional/users/src/Listeners/` fermant toutes les sessions au changement de mot de passe (FR-012). La poussée vers les applications ouvertes est T121 (US5)
- [X] T065 [US1] Composant Livewire `Account` + vue + route `GET /account` dans `api/technical/oidc/src/Livewire/Account.php` : consultation et modification de son propre profil et de son mot de passe, sans passer par un administrateur (FR-013)
- [X] T066 [US1] Journalisation via `RecordSecurityEvent` depuis `api/technical/oidc/src/Listeners/RecordAuthenticationEvents.php` : `authentication_succeeded`, `authentication_failed`, `password_changed`, `password_reset_requested`

**Checkpoint**: US1 est démontrable seule — un compte, une application, une connexion, un retour
exact. C'est le MVP.

---

## Phase 4: User Story 2 - Savoir à quoi un utilisateur a droit (Priority: P2)

**Goal**: le point central répond les applications atteignables et les rôles détenus, sans qu'aucune
application ne tienne son annuaire.

**Independent Test**: deux applications déclarées, deux utilisateurs aux droits différents, aucun
écran à écrire — on interroge le point central pour chacun et on compare aux droits attribués.

### Tests for User Story 2

- [X] T067 [P] [US2] Feature test de `/me/applications` dans `api/functional/licensing/tests/Feature/MyApplicationsTest.php` : trois licences et deux accès → exactement ces deux applications ; aucun droit → `200` avec `data: []`, **jamais une erreur** ; licence expirée → application absente
- [X] T068 [P] [US2] Feature test des claims dans `api/technical/oidc/tests/Feature/IdTokenClaimsTest.php` : `roles` ne contient que les rôles de **l'application appelante**, `sid` présent, `organization` présent sous le scope `profile`
- [X] T069 [P] [US2] Feature test des refus hors périmètre dans `api/technical/oidc/tests/Feature/ScopeIsolationTest.php` : une application qui demande les rôles d'un tiers ou les accès sur une autre application est refusée (FR-017)

### Implementation for User Story 2

- [X] T070 [US2] Fournisseur de claims implémentant le contrat T038, dans `api/functional/licensing/src/Oidc/LicensingClaimsProvider.php`, enregistré par `LicensingServiceProvider` — c'est le fonctionnel qui se branche sur le technique
- [X] T071 [US2] Claim `organization` (`{ id, name }` de l'organisation de rattachement) sous le scope `profile`, dans `api/functional/licensing/src/Oidc/LicensingClaimsProvider.php`
- [X] T072 [US2] Claim `roles` sous le scope `applications`, réduit aux clés des rôles détenus **sur l'application appelante uniquement** (FR-016, FR-017), dans `api/functional/licensing/src/Oidc/LicensingClaimsProvider.php`
- [X] T073 [US2] Déclarer les scopes `openid`, `profile`, `email`, `applications` dans `api/technical/oidc/config/`
- [X] T074 [US2] Endpoint `GET /me/applications` dans `api/functional/licensing/src/Http/Controllers/MyApplicationsController.php` et sa route dans `api/routes/api.php` — **contrôleur écrit à la main, pas une ressource lomkit** : la réponse croise licence valide (T028), accès attribué, état du compte et état de l'organisation, et ne projette aucune table. Renvoie `slug`, `name`, `logo_url`, `home_url` (FR-015)
- [X] T075 [US2] `/oauth/userinfo` renvoyant les mêmes claims filtrés par les scopes accordés, dans `api/technical/oidc/src/Http/Controllers/UserInfoController.php`
- [X] T076 [US2] Aucune mise en cache de la réponse de droits : toute modification est reflétée dès la demande suivante (FR-019) — à vérifier dans `api/functional/licensing/src/Http/Controllers/MyApplicationsController.php` et `api/functional/licensing/src/Oidc/LicensingClaimsProvider.php`
- [X] T077 [US2] Endpoints `GET /me` et `PATCH /me` dans `api/functional/users/src/Http/Controllers/ProfileController.php` — l'écran `/account` sert l'utilisateur devant son navigateur, ces endpoints servent une application agissant en son nom avec un `access_token`

**Checkpoint**: US1 et US2 fonctionnent chacune indépendamment.

---

## Phase 5: User Story 3 - Gouverner les organisations, les licences et les accès (Priority: P2)

**Goal**: les opérations, les règles et les données que l'application d'administration manipulera —
ce produit ne livre pas ses écrans.

**Independent Test**: sans aucun écran, en enchaînant les opérations exposées — créer une
organisation, une licence, un utilisateur, accorder puis retirer un accès, et constater à chaque
étape le changement dans ce que le point central répond.

### Tests for User Story 3

- [X] T078 [P] [US3] Feature test des sièges dans `api/functional/licensing/tests/Feature/SeatLimitTest.php` : dépassement → `409 seats_exhausted` ; deux attributions concurrentes du dernier siège → une seule passe (le verrou de T093)
- [X] T079 [P] [US3] Feature test du périmètre dans `api/functional/organizations/tests/Feature/TenantScopeTest.php` : un administrateur Acme lisant ou écrivant sur Globex → `403`, en lecture comme en écriture (FR-028)
- [X] T080 [P] [US3] Feature test du dernier administrateur dans `api/functional/users/tests/Feature/LastAdminTest.php` : désactiver ou rétrograder le seul `admin` `active` → `409 last_admin`
- [X] T081 [P] [US3] Feature test des invitations dans `api/functional/users/tests/Feature/InvitationTest.php` : adresse déjà rattachée → `409 email_already_attached` ; invitation expirée ou déjà acceptée → `410` ; invitation plus récente invalidant la précédente
- [X] T082 [P] [US3] Feature test d'enchaînement dans `api/functional/licensing/tests/Feature/GovernanceFlowTest.php` : accorder un accès puis réinterroger `/me/applications` → la nouvelle application y figure ; licence expirée → elle en sort

### Implementation for User Story 3

- [X] T083 [US3] Migration et modèle `Invitation` dans `api/functional/users/` : `id` UUID, `email` string(255) requis, `organization_id` FK requis, `organization_role`, `invited_by_id` FK User, `token_hash` **haché — le jeton en clair n'existe que dans le courriel**, `expires_at` de durée configurable, `accepted_at` nullable (usage unique : renseigné, l'invitation ne vaut plus), `timestamps`
- [X] T084 [US3] `Control` de `lomkit/laravel-access-control` par modèle dans chaque couche (`api/functional/organizations/src/Rest/Controls/`, `api/functional/users/src/Rest/Controls/`, `api/functional/catalog/src/Rest/Controls/`, `api/functional/licensing/src/Rest/Controls/`, `api/technical/audit/src/Rest/Controls/`), périmètre « ma seule organisation » pour un administrateur client — jamais un test sur un nom de rôle
- [X] T085 [P] [US3] Resource lomkit `OrganizationResource` dans `api/functional/organizations/src/Rest/Resources/` : exploitant tout, administrateur client en lecture sur la sienne
- [X] T086 [P] [US3] Resource lomkit `UserResource` dans `api/functional/users/src/Rest/Resources/` : exploitant tout, administrateur client restreint à sa seule organisation
- [X] T087 [P] [US3] Resources lomkit `ApplicationResource` et `ApplicationRoleResource` dans `api/functional/catalog/src/Rest/Resources/` : exploitant tout, autres en lecture des `published`
- [X] T088 [P] [US3] Resources lomkit `LicenseResource` et `ApplicationAccessResource` dans `api/functional/licensing/src/Rest/Resources/`
- [X] T089 [P] [US3] Resource lomkit `SecurityEventResource` dans `api/technical/audit/src/Rest/Resources/` — **lecture seule**, périmètre de l'appelant (FR-038)
- [X] T090 [US3] `api/routes/api.php` : `Rest::resource(...)` pour les ressources ci-dessus et les routes non-CRUD. URIs au pluriel, imbrication d'**un niveau au plus** — `/organizations/{id}/licenses` pour la collection, `/licenses/{id}` pour le membre. **Aucun contrôleur CRUD écrit à la main**
- [X] T091 [US3] Attribution d'un accès dans `api/functional/licensing/src/Actions/GrantApplicationAccess.php` : transaction verrouillant la ligne de licence (`lockForUpdate`) **avant** de compter les sièges occupés — le plus petit périmètre qui rende FR-024 vraie. Sièges occupés = nombre d'`ApplicationAccess` sur cette application dont l'utilisateur appartient à l'organisation et n'est pas `disabled`
- [X] T092 [US3] Invariant d'attribution : un accès ne peut exister que si l'organisation détient une licence valide sur l'application. Vérifié à l'attribution ; **la perte de validité ultérieure ne supprime pas l'accès, elle le rend inopérant** — FR-023 se lit au moment de la question, pas en base. Dans `api/functional/licensing/src/Actions/GrantApplicationAccess.php`
- [X] T093 [US3] Règle du dernier administrateur actif dans `api/functional/users/src/Actions/DisableUser.php` : une organisation garde au moins un `admin` en statut `active` (FR-029)
- [X] T094 [US3] Refus explicite d'inviter une adresse déjà rattachée à une organisation (FR-026), dans `api/functional/users/src/Actions/InviteUser.php` — ni compte fantôme, ni déplacement silencieux de la personne
- [X] T095 [US3] Refus d'attribuer un `ApplicationRole` n'appartenant pas à l'application de l'accès, dans `api/functional/licensing/src/Actions/AssignApplicationRoles.php`
- [X] T096 [US3] Endpoints de transition dans `api/routes/api.php` et les contrôleurs de couche : `POST /organizations/{id}/suspend`, `POST /organizations/{id}/activate`, `POST /users/{id}/disable`, `POST /users/{id}/enable`, `POST /users/{id}/resend-invitation` — des **actions nommées**, pas un `PATCH status`, pour qu'une transition illégale soit indéclenchable
- [X] T097 [US3] Suspension d'organisation coupant l'accès de **tous** ses utilisateurs, administrateurs compris (FR-021), et révoquant les sessions vivantes, dans `api/functional/organizations/src/Actions/SuspendOrganization.php`
- [X] T098 [US3] Composant Livewire `AcceptInvitation` + vue + routes `GET /invitations/{token}` (**`410` si expirée ou déjà acceptée**) et `POST /invitations/{token}` dans `api/technical/oidc/src/Livewire/AcceptInvitation.php` : définit le mot de passe, fait passer le compte de `invited` à `active` et ouvre la session dans la foulée
- [X] T099 [US3] Notification d'invitation dans `api/functional/users/src/Notifications/UserInvited.php`
- [X] T100 [US3] Codes de réponse du contrat dans `api/technical/framework/src/Exceptions/Handler.php` et les exceptions métier de chaque couche : `401` jeton absent/expiré/révoqué, `403` hors périmètre, `409` règle métier avec **code machine** (`seats_exhausted`, `last_admin`, `email_already_attached`, `illegal_transition`), `422` validation, `429` limitation — un code machine, pas un message à analyser
- [X] T101 [US3] `SecurityEvent` émis par chaque action de `api/functional/*/src/Actions/` sur **chaque** écriture de gouvernance : `access_granted`, `access_revoked`, `user_disabled`, `user_enabled`, `organization_suspended`, `license_attached`, `license_revoked`, `invitation_sent`, `invitation_accepted`

**Checkpoint**: US1, US2 et US3 fonctionnent chacune indépendamment.

---

## Phase 6: User Story 4 - Raccorder une nouvelle application à l'écosystème (Priority: P3)

**Goal**: déclarer une application la rend immédiatement raccordable, sans modifier ni redéployer le
point central ni aucune application déjà en place.

**Independent Test**: déclarer une application factice et constater qu'elle mène une connexion à son
terme sans aucune intervention sur le point central.

### Tests for User Story 4

- [X] T102 [P] [US4] Feature test dans `api/functional/catalog/tests/Feature/ApplicationOnboardingTest.php` : déclarer, publier, puis mener un flux d'identification complet avec ce nouveau client **sans toucher à la configuration ni redéployer**
- [X] T103 [P] [US4] Feature test dans `api/functional/catalog/tests/Feature/ClientSecretRotationTest.php` : après rotation l'ancien secret est refusé, les autres applications continuent de fonctionner ; le secret n'est **affiché qu'une seule fois**
- [X] T104 [P] [US4] Feature test dans `api/functional/catalog/tests/Feature/ApplicationRetirementTest.php` : une application retirée disparaît des droits répondus, **sans que l'historique de ses accès passés soit perdu**

### Implementation for User Story 4

- [X] T105 [US4] Création du client Passport à la déclaration d'une application dans `api/functional/catalog/src/Actions/DeclareApplication.php` : secret haché en base, renvoyé **une seule fois**, jamais relisible
- [X] T106 [US4] Endpoints `POST /applications/{id}/client-secret` (rotation, secret renvoyé une seule fois) et `DELETE /applications/{id}/client-secret` (révocation) — opérations par application, **sans effet sur les autres** (FR-033) — `api/functional/catalog/src/Http/Controllers/ClientSecretController.php` et `api/routes/api.php`
- [X] T107 [US4] Endpoints `POST /applications/{id}/publish` et `POST /applications/{id}/retire` avec les transitions gardées : `draft → published`, `published → retired`, `retired → published` ; **`retired → draft` refusée** — `api/functional/catalog/src/Http/Controllers/ApplicationLifecycleController.php` et `api/functional/catalog/src/Models/Concerns/`
- [X] T108 [US4] Gestion des adresses de retour sur `oauth_clients.redirect_uris` depuis la ressource Application — jamais dupliquées sur la table `applications`, redoubler la liste garantirait qu'un jour les deux divergent — `api/functional/catalog/src/Rest/Resources/ApplicationResource.php`
- [X] T109 [US4] Retrait du catalogue excluant l'application des droits répondus par T074 et T072, **sans supprimer les `ApplicationAccess` passés** (FR-032), par l'expression de validité de `api/functional/licensing/src/Models/Concerns/`
- [X] T110 [US4] Listener sur l'événement `deleting` d'un `ApplicationRole` détachant les attributions correspondantes, parcours au `cursor()` — **aucun `onDelete('cascade')`**, sinon les listeners des lignes enfants sont silencieusement sautés — `api/functional/catalog/src/Listeners/DetachRolesOnApplicationRoleDeleting.php`
- [X] T111 [US4] `SecurityEvent` `application_published`, `application_retired` et `client_secret_rotated` émis depuis `api/functional/catalog/src/Actions/`
- [X] T112 [US4] Un client dont le secret est révoqué est rejeté par le point central **sans effet sur les autres applications raccordées** — `api/functional/catalog/src/Actions/RevokeClientSecret.php`

**Checkpoint**: les quatre premières histoires fonctionnent chacune indépendamment.

---

## Phase 7: User Story 5 - Fermer une session partout, couper un accès tout de suite (Priority: P3)

**Goal**: une déconnexion depuis n'importe quelle application ferme la session centrale, et une
désactivation coupe l'accès partout sous une minute (SC-005).

**Independent Test**: deux applications ouvertes simultanément — se déconnecter depuis l'une et
vérifier l'autre ; puis désactiver un compte avec des sessions ouvertes et mesurer le délai de coupure.

### Tests for User Story 5

- [X] T113 [P] [US5] Feature test dans `api/technical/oidc/tests/Feature/GlobalLogoutTest.php` : deux applications ouvertes, déconnexion depuis l'une → l'autre ne reconnaît plus l'utilisateur à l'action suivante
- [X] T114 [P] [US5] Feature test dans `api/technical/oidc/tests/Feature/BackchannelLogoutPushTest.php` : à la désactivation d'un compte, la poussée part vers **chaque participant** de la session et l'accès est refusé en moins d'une minute
- [X] T115 [P] [US5] Feature test dans `api/technical/oidc/tests/Feature/LogoutPushFailureTest.php` : une `backchannel_logout_url` injoignable est journalisée en `logout_push_failed` et **ne bloque pas** les autres applications, qui sont prévenues quand même
- [X] T116 [P] [US5] Feature test dans `api/technical/oidc/tests/Feature/RefreshTokenRevalidationTest.php` : compte désactivé, organisation suspendue ou licence tombée → `invalid_grant` au rafraîchissement
- [X] T117 [P] [US5] Feature test dans `api/technical/oidc/tests/Feature/SessionExpiryTest.php` : inactivité au-delà de la durée → réidentification exigée ; expiration absolue atteinte → idem

### Implementation for User Story 5

- [X] T118 [US5] Route `POST /logout` dans `api/technical/oidc/routes/web.php` : ferme la session Laravel, marque la `SsoSession` révoquée et met en file la poussée vers chaque participant. Une application la déclenche en y renvoyant l'utilisateur (FR-034)
- [X] T119 [US5] Enregistrement d'un `SsoSessionParticipant` à chaque autorisation réussie — c'est la liste exacte des applications à prévenir (FR-035) — `api/technical/oidc/src/Listeners/RecordSessionParticipant.php`
- [X] T120 [US5] Construction du `logout_token` signé dans `api/technical/oidc/src/Actions/BuildLogoutToken.php` : claims `iss`, `aud`, `iat`, `jti`, `sid`, `sub`, `events: { "http://schemas.openid.net/event/backchannel-logout": {} }` et `reason` parmi `logout`, `user_disabled`, `organization_suspended`, `license_revoked`, `password_changed`
- [X] T121 [US5] Job de poussée dans `api/technical/oidc/src/Jobs/PushBackchannelLogout.php` : `POST` vers `application.backchannel_logout_url` en `Content-Type: application/jwt`, réessais exponentiels, ordonnancement déterministe, échec définitif journalisé en `logout_push_failed`. Une application injoignable ne bloque pas les autres
- [X] T122 [US5] Brancher les cinq déclencheurs sur la poussée et la révocation des jetons : déconnexion (FR-034), désactivation de compte (FR-036), suspension d'organisation (FR-021), résiliation de licence (FR-023), changement de mot de passe (FR-012) — listeners dans `api/technical/oidc/src/Listeners/` et `api/functional/*/src/Listeners/`, déclarés dans les service providers de couche
- [X] T123 [US5] Révocation des jetons Passport concernés en même temps que la poussée — un `access_token` JWT validé localement via le JWKS ne voit jamais sa révocation en base, d'où la poussée — `api/technical/oidc/src/Actions/RevokeSessionTokens.php`
- [X] T124 [US5] Revalidation de l'état du compte, de l'organisation **et** de la licence à chaque usage d'un `refresh_token` : l'une des trois est tombée → `invalid_grant`, et l'application doit renvoyer vers `/oauth/authorize` — `api/technical/oidc/src/Listeners/RevalidateOnRefresh.php`
- [X] T125 [US5] Application sans `backchannel_logout_url` : comportement explicite et journalisé — elle ne reçoit pas la poussée et ne tient que par la durée de vie du jeton, limite assumée de SC-005 — `api/technical/oidc/src/Jobs/PushBackchannelLogout.php`
- [X] T126 [US5] `SecurityEvent` `session_ended` et `logout_push_failed` émis depuis `api/technical/oidc/src/Jobs/PushBackchannelLogout.php` et `api/technical/oidc/src/Actions/`

**Checkpoint**: les cinq histoires sont livrées et testables indépendamment.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T127 [P] Revue des fichiers de traduction `api/technical/oidc/lang/` et des couches fonctionnelles — aucun texte utilisateur en dur nulle part
- [X] T128 [P] Formater tout le diff depuis `api/` : `./vendor/bin/sail exec laravel.test vendor/bin/pint --dirty --format agent`
- [X] T129 Purges planifiées dans `api/routes/console.php` : `passport:purge` pour les jetons expirés et `model:prune` pour les `SecurityEvent` au-delà de douze mois, **par lots**
- [X] T130 Limitation de débit sur les routes d'api renvoyant `429`, cohérente avec le throttle d'identification de T053 — `api/routes/api.php` et `api/technical/framework/src/Providers/FrameworkServiceProvider.php`
- [X] T131 Vérifier les objectifs du plan : `/oauth/token` sous 300 ms au p95, bascule d'une application à l'autre sous 5 s (SC-002), en instrumentant les routes de `api/technical/oidc/routes/`
- [X] T132 Relancer `sail artisan osdd:phpunit` depuis `api/`, vérifier `api/phpunit.xml`, puis la suite complète `./vendor/bin/sail test` — toutes les couches passent
- [ ] T133 Dérouler [quickstart.md](./quickstart.md) de bout en bout, les cinq blocs de scénarios, depuis la racine du workspace avec `api/` démarré sous Sail
- [ ] T134 Vérifier avec `git -C mobile status` qu'**aucun commit n'a atterri dans `mobile`** (research.md D14), et que `api` est sur sa branche de feature, propre et poussée — `speckit.multirepo.status` rend ce rapport par dépôt

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** : aucune dépendance. T009 est bloquante — si une vue Livewire ne peut pas être servie depuis une couche OSDD, tout le placement des écrans est à rediscuter.
- **Foundational (Phase 2)** : dépend de la Phase 1. **Bloque toutes les user stories.**
- **US1 (Phase 3)** : dépend de la Phase 2. Aucune dépendance sur une autre histoire.
- **US2 (Phase 4)** : dépend de la Phase 2. Testable sans US1 (jetons émis directement), mais se démontre mieux après.
- **US3 (Phase 5)** : dépend de la Phase 2. Indépendante d'US1 et d'US2.
- **US4 (Phase 6)** : dépend de la Phase 2. Son test de bout en bout (T102) rejoue un flux d'identification, donc se valide pleinement après US1.
- **US5 (Phase 7)** : dépend de la Phase 2. T122 branche des déclencheurs posés en US3 (désactivation, suspension) et en US4 (résiliation) — les brancher au fil de l'eau si ces histoires sont déjà livrées, sinon les poser dans US5 et les câbler après.
- **Polish (Phase 8)** : dépend des histoires retenues.

### Ordre à l'intérieur d'une couche

Enums → migrations → modèles → factories → règles et actions → ressources et contrôleurs → routes.
Les tests d'une histoire sont écrits avant son implémentation et doivent échouer d'abord.

### Parallel Opportunities

- **Phase 1** : T002 à T006, cinq couches, cinq arborescences disjointes.
- **Phase 2** : les enums (T012, T017, T022, T030) en parallèle ; les factories (T015, T021, T025, T029) en parallèle une fois leurs modèles posés ; les quatre couches fonctionnelles avancent en parallèle jusqu'à ce que `users` ait besoin d'`Organization` (T018 après T013).
- **Phase 3 à 7** : tous les tests marqués [P] d'une même histoire, écrits ensemble.
- **Phase 5** : les six ressources lomkit (T085 à T089) en parallèle, une par fichier.
- **Entre histoires** : une fois la Phase 2 finie, US1, US2, US3 et US4 peuvent être tenues par quatre personnes différentes.

---

## Parallel Example: User Story 1

```bash
# Les cinq tests d'US1 ensemble :
Task: "Feature test du parcours complet dans api/technical/oidc/tests/Feature/AuthorizationCodeFlowTest.php"
Task: "Feature test des refus dans api/technical/oidc/tests/Feature/AuthorizationRefusalTest.php"
Task: "Livewire test de l'écran de connexion dans api/technical/oidc/tests/Feature/LoginScreenTest.php"
Task: "Feature test du mot de passe oublié dans api/technical/oidc/tests/Feature/PasswordResetTest.php"
Task: "Unit test des transitions du compte dans api/functional/users/tests/Unit/UserStateTest.php"
```

---

## Implementation Strategy

### MVP First (User Story 1 seule)

1. Phase 1 — Setup, **T009 en premier** : le placement des écrans en dépend
2. Phase 2 — Foundational, bloquante
3. Phase 3 — US1
4. **STOP et VALIDER** : jouer le bloc US1 de [quickstart.md](./quickstart.md)
5. Un collaborateur se connecte une fois et atteint deux applications : la raison d'être du produit tient

### Incremental Delivery

1. Setup + Foundational → socle
2. US1 → **MVP**, la connexion unique
3. US2 → les droits exposés, le portail devient possible
4. US3 → la gouvernance, l'écosystème dépasse la démonstration
5. US4 → le raccordement en libre-service
6. US5 → la révocation immédiate, qui referme le risque concentré

### Parallel Team Strategy

Une fois la Phase 2 finie : une personne sur US1 (le chemin critique), une sur US3 (la plus volumineuse
et la plus indépendante), une sur US2 puis US4. US5 en dernier, parce qu'elle se branche sur les
déclencheurs posés par les autres.

---

## Notes

- **Un seul dépôt**, `api`, donc **une seule merge request** : la séquence de fusion inter-dépôts du `CLAUDE.md` du workspace ne s'applique pas. Rien dans `mobile`.
- Toutes les commandes passent par `./vendor/bin/sail`, jamais sur l'hôte.
- `sail artisan osdd:phpunit` après **chaque** couche créée, sinon ses tests ne sont pas exécutés.
- Les commandes `osdd:*` ciblent une couche ; les `make:*` écrivent dans un `app/` qui n'existe pas.
- Pas de commentaires dans le code ; le code est en anglais, cette liste en français.
- Pas de `onDelete('cascade')`, pas d'observers, pas d'enum MySQL, pas de HTML dans du PHP, pas de texte utilisateur en dur.
- Commit après chaque tâche ou groupe cohérent ; s'arrêter à chaque checkpoint pour valider l'histoire seule.
