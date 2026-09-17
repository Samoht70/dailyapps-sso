# Implementation Plan: Authentification centralisée (SSO) de l'écosystème DailyApps

**Branch**: `001-sso-central-authentication` | **Date**: 2026-09-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-sso-central-authentication/spec.md`

## Summary

Faire de `dailyapps-sso` le fournisseur d'identité unique de l'écosystème : un seul écran de
connexion, une seule session, et la source de vérité de qui a le droit d'entrer où — organisations
clientes, licences, sièges, accès applicatifs et rôles.

L'approche retenue est **OpenID Connect sur OAuth 2.0**, flux *authorization code* avec PKCE,
construit dans l'api Laravel avec `laravel/passport` ^13.8 et `jeremy379/laravel-openid-connect`
^3.3, plutôt qu'avec un fournisseur d'identité externe : le cœur de valeur est la relation
organisation × licence × accès, et la déporter dans un produit tiers créerait deux sources de vérité
à synchroniser.

**Un seul dépôt livre cette feature.** Les cinq écrans du point central — connexion, mot de passe
oublié, réinitialisation, invitation, profil — sont des composants Livewire servis par la même
application que `/oauth/authorize`. Le dépôt `front` (Nuxt) a été retiré du workspace : le portail et
l'administration étant hors périmètre, il ne lui restait que ces cinq formulaires, et les séparer
imposait un domaine parent partagé, une session inter-origines et un second déployable pour rien.
Le dépôt `mobile` n'est pas touché.

Le détail des arbitrages est dans [research.md](./research.md).

## Affected Repos

<!-- speckit-multirepo:begin -->

| Repo | Rôle dans la feature |
|------|----------------------|
| api  | Livre la totalité de la feature : couches OSDD, écrans Livewire, /oauth/* |

<!-- speckit-multirepo:end -->

`mobile` n'est pas touché : aucun commit ne doit y atterrir.

## Technical Context

**Language/Version**: PHP 8.4. Dart 3.13 dans `mobile`, non touché.

**Primary Dependencies**: Laravel 13.17, `xefi/laravel-osdd` ^2.0, `lomkit/laravel-rest-api` ^2.23,
`lomkit/laravel-access-control` ^0.5, `spatie/laravel-permission` ^8.3. **À ajouter** :
`laravel/passport` ^13.8, `jeremy379/laravel-openid-connect` ^3.3, `livewire/livewire` ^4.4.
Tailwind 4 et Vite 8 sont déjà en place dans `api/package.json`.

**Storage**: MySQL 8.4 via Laravel Sail. Sessions, cache et file d'attente déjà en base
(`technical/framework`). La file d'attente porte la poussée de déconnexion.

**Testing**: PHPUnit 12.5 via `./vendor/bin/sail test`, un seul lanceur pour tout — les écrans
Livewire se testent avec `Livewire::test(...)` dans la même suite. Factories par le helper `faker()`
de `xefi/faker-php-laravel`. `osdd:phpunit` resynchronise `phpunit.xml` après chaque nouvelle couche.

**Target Platform**: serveur Linux conteneurisé ; navigateurs de bureau et mobiles pour les écrans.

**Performance Goals**: `/oauth/token` sous 300 ms au p95 ; connexion complète sous 30 s (SC-003) ;
bascule d'une application à l'autre sous 5 s (SC-002) ; propagation d'une révocation sous 60 s
(SC-005).

**Constraints**: le point central est un point de défaillance unique pour quinze applications —
99,9 % de disponibilité visés (SC-006). Durées de vie : `access_token` 15 min, `refresh_token` 8 h
avec rotation. Aucune contrainte de domaine partagé : les écrans et `/oauth/authorize` sont servis
par la même application.

**Scale/Scope**: ~15 applications raccordées, 2 000 sessions simultanées (SC-007). 6 couches OSDD —
2 existantes étendues, 4 nouvelles.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**La porte n'a pas pu se fermer : il n'y a pas de constitution.** `.specify/memory/constitution.md`
est encore le gabarit vierge livré par `specify init` — `[PRINCIPLE_1_NAME]`, `[SECTION_2_CONTENT]`,
`[GOVERNANCE_RULES]`. Aucun principe n'y est ratifié, donc aucun ne peut être violé, et le contrôle
ne prouve rien. Je le signale plutôt que de cocher une case vide.

Ce qui joue le rôle de garde-fou en attendant, et que ce plan respecte :

| Contrainte de fait | Origine | Comment le plan s'y tient |
|--------------------|---------|---------------------------|
| Laravel + Livewire est la stack par défaut | `global:default-project-stack` | plus de dérogation Nuxt ; les écrans sont Livewire dans l'api |
| Architecture en couches OSDD | `laravel:osdd-scaffolding`, échafaudage existant | 6 couches, aucune fonctionnalité hors couche, pas de `app/` à la racine |
| Cinq paquets obligatoires | `laravel:preferred-packages` | déjà installés ; CRUD par `lomkit/laravel-rest-api`, périmètres par `lomkit/laravel-access-control`, factories par `faker()` |
| Vérification par permission, jamais par nom de rôle | `laravel:permissions-not-roles` | D6 sépare permissions spatie et rôles applicatifs |
| Pas de cascade en base | `laravel:no-cascade-delete` | aucun `onDelete('cascade')` ; cycles de vie plutôt que suppressions |
| Pas d'observers | `laravel:no-observers` | événements + listeners déclarés dans les service providers de couche |
| Pas de HTML dans du PHP | `laravel:no-html-in-php` | le balisage vit en Blade, jamais concaténé dans une classe |
| Pas de texte en dur | `laravel:no-hardcoded-user-text` | les messages des cinq écrans passent par les fichiers de traduction |
| Pas de documentation projet | `global:no-project-docs` | rien créé hors `specs/` ; le `CLAUDE.md` du workspace est mis à jour, pas augmenté |
| Toute fonctionnalité neuve est testée | `global:test-new-features` | D13, une seule suite PHPUnit |
| `staging` est le tronc | `CLAUDE.md` du workspace | branche coupée de `staging` par `speckit.multirepo.branch` |

**Action recommandée avant `/speckit-implement`** : lancer `/speckit-constitution` pour ratifier ces
principes. Un SSO est la brique où une règle non écrite coûte le plus cher.

**Re-contrôle après phase 1** : inchangé. La conception n'introduit aucun écart à ces contraintes, et
la bascule en monolithe en lève une — la dérogation à la stack par défaut.

## Project Structure

### Documentation (this feature)

```text
specs/001-sso-central-authentication/
├── plan.md              # ce fichier
├── spec.md              # /speckit-specify
├── research.md          # phase 0 — 14 décisions
├── data-model.md        # phase 1
├── quickstart.md        # phase 1
├── contracts/           # phase 1
│   ├── oidc-provider.md     # surface OIDC exposée aux 15 applications
│   ├── admin-api.md         # gouvernance + « mes applications »
│   └── session-api.md       # les cinq écrans du point central
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks — pas créé ici
```

### Source Code (repository root)

```text
api/                                      # Laravel 13 + Livewire, couches OSDD — pas de app/ à la racine
├── functional/
│   ├── users/                            # EXISTANTE — étendue
│   │   ├── src/Models/                       User (+ organization_id, status, organization_role), Invitation
│   │   ├── src/States/                       patron State du cycle de vie du compte
│   │   ├── src/Enums/                        UserStatus, OrganizationRole
│   │   ├── src/Listeners/                    fermeture des sessions au changement de mot de passe
│   │   ├── src/Notifications/                invitation, réinitialisation
│   │   ├── src/Rest/                         Resource lomkit + Control
│   │   ├── database/migrations/
│   │   └── tests/
│   ├── organizations/                    # NOUVELLE
│   ├── catalog/                          # NOUVELLE — Application, ApplicationRole
│   └── licensing/                        # NOUVELLE — License, ApplicationAccess, « mes applications »
├── technical/
│   ├── framework/                        # EXISTANTE — inchangée
│   ├── permissions/                      # EXISTANTE — permissions de l'api seulement
│   ├── osdd/                             # EXISTANTE — inchangée
│   ├── oidc/                             # NOUVELLE — Passport + OIDC, claims, back-channel logout
│   │   ├── src/Contracts/                    point d'extension : fournisseur de claims
│   │   ├── src/Models/                       SsoSession, SsoSessionParticipant, Client (Passport étendu)
│   │   ├── src/Jobs/                         poussée de déconnexion, réessais
│   │   └── src/Livewire/                     Login, ForgotPassword, ResetPassword, AcceptInvitation
│   │   └── resources/views/                  les vues Blade de ces composants
│   └── audit/                            # NOUVELLE — SecurityEvent, rétention Prunable
├── resources/views/                      # EXISTANT — layout applicatif, déjà câblé Vite + Tailwind 4
├── routes/web.php                        # les cinq écrans
└── routes/api.php                        # Rest::resource(...) + routes non-CRUD

mobile/                                   # NON TOUCHÉ par cette feature
```

**Structure Decision**: un seul dépôt actif, `api`. Tout le métier vit dans des couches OSDD — pas de
`app/` à la racine, `osdd:start` l'a supprimé, et chaque couche est un paquet Composer local déclaré
dans `api/composer.json`. Les écrans Livewire vivent dans `technical/oidc`, la couche qui détient déjà
la session et le flux d'identification : les mettre ailleurs séparerait l'écran de la règle qu'il
applique.

**Point à vérifier sur la première couche qui porte une vue** : la documentation de
`xefi/laravel-osdd` ne mentionne ni vues, ni Blade, ni Livewire, ni routes — elle décrit une couche
comme possédant « models, migrations, seeders ». Le service provider de couche peut appeler
`loadViewsFrom()` et enregistrer des composants Livewire comme n'importe quel paquet Composer, donc
cela fonctionnera ; mais c'est un usage que sa documentation ne couvre pas. À éprouver tôt.

**Un seul dépôt, donc une seule merge request.** La séquence de fusion inter-dépôts décrite dans le
`CLAUDE.md` du workspace ne s'applique pas ici. `speckit.multirepo.branch` branche par défaut tous les
dépôts de `repos.yml` — il en reste deux, et **aucun commit ne doit atterrir dans `mobile`**.

## Complexity Tracking

Pas de violation à justifier : il n'y a pas de constitution à violer (voir Constitution Check). Deux
écarts au « tout vient d'un paquet » méritent toutefois d'être tracés ici, parce qu'ils représentent
l'essentiel du code non trivial à écrire.

| Écart | Pourquoi nécessaire | Alternative plus simple, et pourquoi écartée |
|-------|---------------------|----------------------------------------------|
| Back-channel logout écrit à la main (`technical/oidc`) | Aucun paquet de l'écosystème Laravel ne le fournit, et un `access_token` JWT validé localement via le JWKS ne voit jamais sa révocation en base. Sans poussée, SC-005 (coupure sous une minute) est hors d'atteinte. | Durée de vie de jeton d'une minute — inexploitable. Introspection à chaque requête — fait du point central un passage obligé et aggrave le risque de SC-006. |
| Endpoint `/me/applications` écrit à la main plutôt qu'une ressource `lomkit` | Ce n'est pas un CRUD : la réponse croise licence valide, accès attribué, état du compte et état de l'organisation. Aucune table ne la projette. | Exposer les accès en CRUD et laisser le portail recomposer la règle — ce serait publier la règle d'accès chez son consommateur, exactement ce que FR-014 refuse. |

## Ce que ce plan laisse ouvert

1. **La constitution n'est pas écrite.** `/speckit-constitution` avant d'implémenter.
2. **Vues et Livewire dans une couche OSDD** ne sont pas documentés en amont. À éprouver sur la
   première couche concernée plutôt qu'à découvrir en fin de parcours.
3. **Le dépôt `mobile` reste déclaré** dans `repos.yml` alors qu'aucune feature ne le vise. Le retirer
   est une décision distincte, à prendre quand la première application métier sera spécifiée.

*La contrainte de domaine parent partagé, ouverte dans la version précédente de ce plan, n'existe
plus : elle était la conséquence du front séparé.*
