# Quickstart — Valider le SSO de bout en bout

**Feature**: [spec.md](./spec.md) | **Contrats**: [contracts/](./contracts/) | **Date**: 2026-09-17

Ce guide sert à **vérifier** la feature une fois implémentée, pas à l'implémenter. Toutes les
commandes se lancent depuis la racine du workspace ; aucune ne suppose un `cd` dans un dépôt enfant.

## Prérequis

- Docker actif — tout tourne sous Laravel Sail, dans le seul dépôt `api`.
- Rien d'autre. Il n'y a ni second déployable, ni domaine parent à arranger : les écrans et
  `/oauth/authorize` sont servis par la même application (voir [research.md](./research.md) D4).

## Démarrer

```bash
(cd api && composer install && cp -n .env.example .env)
git -C api status --short                     # rien ne doit traîner avant de commencer
./api/vendor/bin/sail up -d
./api/vendor/bin/sail artisan key:generate
./api/vendor/bin/sail artisan migrate
./api/vendor/bin/sail artisan passport:keys   # clés de signature des jetons
./api/vendor/bin/sail artisan db:seed         # organisation exploitant, compte d'amorçage
./api/vendor/bin/sail npm run build           # Vite + Tailwind 4 pour les écrans
```

L'application sert sur `http://localhost` via Sail. La file d'attente doit tourner, sinon la poussée
de déconnexion du scénario US5 ne partira jamais :

```bash
./api/vendor/bin/sail artisan queue:work
```

## La suite de tests

```bash
./api/vendor/bin/sail test
```

Une seule suite pour tout, écrans compris — les composants Livewire se testent avec
`Livewire::test(...)`. Après avoir créé une couche, resynchroniser :

```bash
./api/vendor/bin/sail artisan osdd:phpunit
```

## Jeu de données d'amorçage

Le seeder pose de quoi rejouer chaque histoire :

- une organisation `operator` (DailyApps) et un compte d'administration ;
- deux organisations clientes, `Acme` et `Globex` ;
- deux applications publiées, `leaves` et `expenses`, chacune exposant les rôles `user` et `manager` ;
- une licence `Acme × leaves` à 2 sièges, une licence `Acme × expenses` expirée ;
- deux utilisateurs Acme : l'un avec accès à `leaves`, l'autre sans aucun accès.

## Scénarios de validation

Chaque bloc valide une user story de la spec et peut se jouer seul.

### US1 — Connexion unique

1. Ouvrir une URL protégée de l'application de démonstration → arrivée sur `/login`, l'URL visée
   conservée par Laravel dans la session (`intended`), pas dans un paramètre d'URL.
2. S'identifier avec l'utilisateur Acme ayant accès à `leaves` → retour **sur l'URL visée**, pas sur
   une page d'accueil.
3. Sans se déconnecter, lancer le flux d'une seconde application → aucun écran de connexion.
4. Rejouer avec un mot de passe faux, puis avec une adresse inconnue → **message identique** dans les
   deux cas.
5. Demander `/oauth/authorize` avec une `redirect_uri` non déclarée → erreur sur le point central,
   **aucune redirection** vers l'adresse fournie.

### US2 — Droits exposés

```bash
curl -H "Authorization: Bearer <access_token>" https://api.sso.localhost/me/applications
```

- Utilisateur Acme avec accès → `leaves` seul. `expenses` est absente : la licence a expiré.
- Utilisateur Acme sans accès → `200` avec `data: []`, **pas** une erreur.
- Décoder l'`id_token` émis pour `leaves` : `roles` ne contient que des rôles de `leaves`, et le claim
  `sid` est présent.

### US3 — Gouvernance

1. Attribuer un troisième accès sur la licence `Acme × leaves` (2 sièges) → `409 seats_exhausted`.
2. Avec le jeton de l'administrateur Acme, lire `/organizations` de Globex → `403`.
3. Désactiver le seul administrateur actif d'Acme → `409 last_admin`.
4. Inviter une adresse déjà rattachée → `409 email_already_attached`.
5. Accorder un accès puis réinterroger `/me/applications` → la nouvelle application y est.

### US4 — Raccorder une application

1. Déclarer une application, la publier, récupérer son secret — affiché **une seule fois**.
2. Mener un flux d'identification complet avec ce nouveau client, sans avoir touché à la
   configuration de l'api ni redéployé quoi que ce soit.
3. Faire tourner le secret → l'ancien est refusé, les autres applications continuent de fonctionner.

### US5 — Déconnexion et révocation

1. Ouvrir deux applications dans deux onglets, se déconnecter depuis l'une → la seconde est refusée à
   l'action suivante.
2. Avec une session vivante, désactiver le compte → vérifier que la poussée part vers chaque
   participant de la session et que l'accès est refusé **en moins d'une minute** (SC-005).
3. Déclarer une `backchannel_logout_url` injoignable, rejouer → l'échec est journalisé en
   `logout_push_failed`, et les autres applications sont prévenues quand même.
4. Changer le mot de passe → toutes les autres sessions tombent.

## Ce que le quickstart ne couvre pas

- La charge de SC-007 (15 applications, 2 000 sessions) : elle demande un tir de charge dédié, pas un
  parcours manuel.
- SC-006 (99,9 % de disponibilité) : se mesure en exploitation, pas à la validation.
- L'application mobile : non touchée par cette feature (research.md D14). Rien ne doit être commité
  dans `mobile`, que `speckit.multirepo.branch` branche pourtant par défaut.
