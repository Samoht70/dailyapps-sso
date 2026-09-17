# Phase 1 — Modèle de données : Authentification centralisée (SSO) DailyApps

**Feature**: [spec.md](./spec.md) | **Recherche**: [research.md](./research.md) | **Date**: 2026-09-17

Le code est en anglais (`laravel:code-in-english`) ; cette note l'est en français. Les états sont des
enums PHP, jamais des colonnes `ENUM` MySQL (`laravel:no-db-enums`). Aucune contrainte
`onDelete('cascade')` : les suppressions passent par des listeners sur l'événement `deleting`
(`laravel:no-cascade-delete`) — mais le modèle est conçu pour qu'on supprime très peu, les cycles de
vie remplaçant la suppression presque partout.

---

## Vue d'ensemble

```text
Organization 1 ──── n User ──── n ApplicationAccess ──── n ApplicationRole
     │                                   │                      │
     │ 1                               n │                      │ n
     └──── n License ──── 1 Application ─┘                      │
                               │ 1                              │
                               └──────────── n ──────────────────
                               │ 1
                               └──── 1 oauth_clients (Passport)

SsoSession 1 ──── n SsoSessionParticipant ──── 1 Application
SecurityEvent (journal, sans relation obligatoire)
```

---

## `functional/organizations`

### Organization

L'entreprise qui souscrit. L'exploitant DailyApps est lui-même une organisation, de nature
`operator` : cela évite un `organization_id` nullable sur les comptes de l'exploitant et rend le
périmètre d'accès uniforme pour tout le monde.

| Champ | Type | Règles |
|-------|------|--------|
| `id` | ULID | |
| `name` | string(160) | requis, unique |
| `kind` | `OrganizationKind` | `operator` \| `client` — exactement une ligne `operator`, garantie par un index unique partiel |
| `status` | `OrganizationStatus` | `active` \| `suspended`, défaut `active` |
| `suspended_at` | datetime? | renseigné en même temps que `status = suspended` |
| `timestamps` | | |

**Relations** : `users` (1-n), `licenses` (1-n).

**Transitions** — bascule simple, gardée, sans patron State (voir D9) :

| De | Vers | Effet |
|----|------|-------|
| `active` | `suspended` | FR-021 : tous les accès des utilisateurs de l'organisation tombent, y compris ceux de ses administrateurs. Les sessions vivantes sont révoquées et poussées. |
| `suspended` | `active` | Les accès redeviennent effectifs sans nouvelle attribution. |

Une organisation `operator` ne peut pas être suspendue — cela couperait l'administration de la
plateforme.

---

## `functional/users` *(couche existante, étendue)*

### User

La table `users` existe déjà (`name`, `email`, `email_verified_at`, `password`, `remember_token`).
Cette feature y ajoute le rattachement, l'état et le rôle dans l'organisation.

| Champ | Type | Règles |
|-------|------|--------|
| `id` | ULID | |
| `organization_id` | FK Organization | **requis** — FR-025, exactement une organisation |
| `name` | string(160) | requis |
| `email` | string(255) | requis, **unique globalement** — FR-026 : une adresse déjà rattachée ne peut pas être invitée ailleurs |
| `password` | string | haché ; nul tant que l'invitation n'est pas acceptée |
| `status` | `UserStatus` | `invited` \| `active` \| `disabled`, défaut `invited` |
| `organization_role` | `OrganizationRole` | `member` \| `admin` |
| `disabled_at` | datetime? | |
| `last_authenticated_at` | datetime? | alimenté à chaque identification réussie |
| `timestamps` | | |

**Le « Rattachement » de la spec n'est pas une table.** Le rattachement étant unique (FR-025), il se
réduit à deux colonnes sur l'utilisateur. Une table de liaison serait une table à une ligne par
utilisateur, et donnerait l'illusion qu'un second rattachement est possible.

**Relations** : `organization` (n-1), `applicationAccesses` (1-n), `ssoSessions` (1-n).

**Transitions** — patron State, une classe par état (D9) :

| De | Vers | Déclencheur | Refusé |
|----|------|-------------|--------|
| `invited` | `active` | acceptation de l'invitation, mot de passe défini | |
| `active` | `disabled` | désactivation par un administrateur | si c'est le dernier administrateur actif de l'organisation (FR-029) |
| `disabled` | `active` | réactivation | |
| `disabled` | `invited` | — | toujours : un compte désactivé ne redevient pas une invitation |

Comportements portés par l'état : peut s'authentifier (`active` seul), apparaît dans les accès
(`active` seul), consomme un siège (`invited` et `active` — un siège est réservé dès l'invitation,
sinon le décompte de FR-024 se contourne en invitant en masse).

**Règles**

- Le mot de passe respecte une exigence minimale de robustesse (FR-009), refusée avec son motif.
- Un changement de mot de passe ferme toutes les sessions (FR-012) et déclenche la poussée D3.
- Une organisation garde au moins un `admin` en statut `active` (FR-029).

### Invitation

| Champ | Type | Règles |
|-------|------|--------|
| `id` | ULID | |
| `email` | string(255) | requis ; refusée si l'adresse est déjà rattachée (FR-026) |
| `organization_id` | FK Organization | requis |
| `organization_role` | `OrganizationRole` | |
| `invited_by_id` | FK User | |
| `token_hash` | string | haché ; le jeton en clair n'existe que dans le courriel |
| `expires_at` | datetime | durée configurable |
| `accepted_at` | datetime? | usage unique : renseigné, l'invitation ne vaut plus |
| `timestamps` | | |

Une invitation plus récente pour la même adresse invalide les précédentes.

La réinitialisation de mot de passe (FR-011) réutilise la table `password_reset_tokens` déjà présente
dans `technical/framework` — même forme : haché, à usage unique, à durée limitée.

---

## `functional/catalog`

### Application

Une application de l'écosystème. Les adresses de retour autorisées ne sont **pas** dupliquées ici :
elles vivent dans `oauth_clients.redirect_uris` de Passport, qui est ce qui les applique réellement
(FR-006). Redoubler la liste, c'est garantir qu'un jour les deux divergent.

| Champ | Type | Règles |
|-------|------|--------|
| `id` | ULID | |
| `slug` | string(64) | requis, unique, kebab-case — l'identifiant stable, porté dans les claims |
| `name` | string(160) | requis |
| `description` | text? | |
| `logo_url` | string? | FR-015 |
| `home_url` | string | requis — où le portail envoie l'utilisateur |
| `backchannel_logout_url` | string? | FR-035 ; absente, l'application ne reçoit pas la poussée et ne tient que par la durée de vie du jeton |
| `status` | `ApplicationStatus` | `draft` \| `published` \| `retired`, défaut `draft` |
| `oauth_client_id` | FK `oauth_clients` | le client Passport correspondant |
| `timestamps` | | |

**Transitions** — enum gardé, sans patron State (D9) :

| De | Vers | Effet |
|----|------|-------|
| `draft` | `published` | entre au catalogue, devient vendable et raccordable |
| `published` | `retired` | FR-032 : disparaît des droits répondus ; les accès passés restent en base |
| `retired` | `published` | remise au catalogue |
| `retired` | `draft` | refusé |

### ApplicationRole

Les rôles qu'une application expose. **Sans rapport avec `spatie/laravel-permission`** (voir D6) :
ceux-là gouvernent l'api du point central, ceux-ci voyagent dans l'`id_token` vers une application
tierce.

| Champ | Type | Règles |
|-------|------|--------|
| `id` | ULID | |
| `application_id` | FK Application | |
| `key` | string(64) | kebab-case, unique **par application** — deux applications peuvent exposer `manager` sans collision |
| `label` | string(160) | requis |
| `description` | text? | |
| `timestamps` | | |

Retirer un rôle encore attribué détache l'attribution correspondante, via un listener sur `deleting`.

---

## `functional/licensing`

### License

| Champ | Type | Règles |
|-------|------|--------|
| `id` | ULID | |
| `organization_id` | FK Organization | |
| `application_id` | FK Application | |
| `starts_on` | date | requis |
| `ends_on` | date? | nul = sans échéance |
| `seats` | unsigned int | requis, ≥ 1 |
| `timestamps` | | |

**Unicité** : `(organization_id, application_id)`. Un renouvellement déplace `ends_on`, il ne crée pas
une seconde licence — sinon « la licence est-elle valide » devient une question à plusieurs réponses.

**Validité** : `starts_on ≤ aujourd'hui` et (`ends_on` nul ou `≥ aujourd'hui`) et l'organisation est
`active` et l'application est `published`. C'est cette expression, et elle seule, qui décide de
FR-019 et FR-023.

**Sièges occupés** : nombre d'`ApplicationAccess` sur cette application dont l'utilisateur appartient
à l'organisation et n'est pas `disabled`. Le contrôle de FR-024 verrouille la ligne de licence
(`lockForUpdate`) avant de compter (D11).

### ApplicationAccess

| Champ | Type | Règles |
|-------|------|--------|
| `id` | ULID | |
| `user_id` | FK User | |
| `application_id` | FK Application | |
| `granted_by_id` | FK User? | qui l'a accordé — FR-038, SC-009 |
| `granted_at` | datetime | |
| `timestamps` | | |

**Unicité** : `(user_id, application_id)`.

**Invariant** : un accès ne peut exister que si l'organisation de l'utilisateur détient une licence
valide sur l'application. Vérifié à l'attribution ; la perte de validité ultérieure ne supprime pas
l'accès — elle le rend inopérant. FR-023 se lit donc au moment de la question, pas en base.

### ApplicationAccessRole *(pivot)*

`application_access_id` × `application_role_id`, unique. Le rôle doit appartenir à l'application de
l'accès — vérifié, sans quoi on attribuerait à quelqu'un un rôle d'une autre application.

---

## `technical/oidc`

### SsoSession

L'identification en cours. Son `id` est le claim `sid` de l'`id_token`, ce qui permet à la poussée de
déconnexion de désigner précisément la session à fermer.

| Champ | Type | Règles |
|-------|------|--------|
| `id` | ULID | devient le `sid` |
| `user_id` | FK User | |
| `laravel_session_id` | string? | la session navigateur du front |
| `ip_address` | string? | |
| `user_agent` | string? | |
| `started_at` | datetime | |
| `last_seen_at` | datetime | alimente l'expiration par inactivité (FR-010) |
| `expires_at` | datetime | expiration absolue (FR-010) |
| `revoked_at` | datetime? | renseigné à la déconnexion, la désactivation, la suspension |

### SsoSessionParticipant

Les applications entrées dans cette session — la liste exacte à prévenir (FR-035).

`sso_session_id` × `application_id`, unique, plus `first_seen_at` et `logout_pushed_at?`.

### Clients Passport

`oauth_clients`, `oauth_access_tokens`, `oauth_refresh_tokens`, `oauth_auth_codes` viennent des
migrations de Passport et ne sont pas redéfinis. Le modèle `Client` est étendu pour que
`skipsAuthorization()` renvoie vrai sur un client *first-party* (D5). Le secret est haché et montré
une seule fois (D12).

---

## `technical/audit`

### SecurityEvent

| Champ | Type | Règles |
|-------|------|--------|
| `id` | ULID | |
| `type` | `SecurityEventType` | voir la liste ci-dessous |
| `actor_id` | FK User? | nul quand l'auteur n'est pas identifié — un échec d'identification, par exemple |
| `organization_id` | FK Organization? | porte le périmètre de lecture de FR-038 |
| `subject_type` / `subject_id` | morph? | l'objet concerné |
| `ip_address` | string? | |
| `user_agent` | string? | |
| `payload` | json | le détail propre au type |
| `created_at` | datetime | pas de `updated_at` : un événement ne se modifie pas |

**`SecurityEventType`** — couvre FR-037 : `authentication_succeeded`, `authentication_failed`,
`authentication_throttled`, `session_ended`, `password_changed`, `password_reset_requested`,
`invitation_sent`, `invitation_accepted`, `access_granted`, `access_revoked`, `user_disabled`,
`user_enabled`, `organization_suspended`, `license_attached`, `license_revoked`,
`application_published`, `application_retired`, `client_secret_rotated`, `logout_push_failed`.

**Rétention** : `Prunable`, douze mois (FR-039), purge par lots et non en masse.

---

## Ce que le modèle laisse hors de lui

- **Pas de table de rattachement** : le rattachement unique tient en deux colonnes (voir `User`).
- **Pas de duplication des adresses de retour** : elles restent sur le client Passport.
- **Pas de suppression en cascade** : les organisations se suspendent, les comptes se désactivent, les
  applications se retirent. Les rares suppressions réelles passent par un listener sur `deleting` qui
  parcourt les enfants au `cursor()`.
- **Pas de rôles applicatifs dans `spatie/laravel-permission`** : deux mécanismes distincts (D6).
