# Contrat — Écrans et session du point central

**Fournisseur et consommateur** : `api`. Ces écrans sont des composants Livewire servis par la même
application que `/oauth/authorize` — il n'y a pas d'appel inter-origines, pas de domaine parent à
arranger, pas de CSRF à négocier entre deux hôtes. Voir [research.md](../research.md) D4.

Ce document décrit donc un **comportement d'écran**, pas une API consommée par un tiers. La surface
appelée de l'extérieur est dans [oidc-provider.md](./oidc-provider.md) et [admin-api.md](./admin-api.md).

## Les cinq écrans

| Route | Écran | Exigences |
|-------|-------|-----------|
| `GET /login` | connexion | FR-001, FR-003, FR-007, FR-008 |
| `GET /password/forgot` | demande de réinitialisation | FR-011 |
| `GET /password/reset/{token}` | définition d'un nouveau mot de passe | FR-009, FR-011, FR-012 |
| `GET /invitations/{token}` | acceptation d'invitation | FR-027 |
| `GET /account` | profil et mot de passe | FR-013 |

## Connexion

`/oauth/authorize` est protégé par le middleware `auth`. Un visiteur non identifié est redirigé vers
`/login` par le mécanisme standard de Laravel, l'URL visée conservée dans la session (`intended`).
Après identification, Laravel y ramène de lui-même : **l'URL de retour n'est jamais reconstruite ni
transportée dans un paramètre**, donc elle ne peut pas être détournée vers un site tiers.

C'est la différence de fond avec un front séparé, où l'URL de retour voyageait en clair dans la query
et devait être revalidée à l'arrivée.

| Issue | Comportement |
|-------|--------------|
| Identifiants valides, compte `active` | session ouverte, redirection vers l'URL visée |
| Identifiants invalides | reste sur `/login`, **message identique** que le compte existe ou non (FR-007) |
| Compte `disabled` ou organisation `suspended` | message distinct — l'utilisateur doit savoir qu'il s'agit d'un compte coupé, pas d'une faute de frappe |
| Trop de tentatives | verrouillage temporaire, sur le compte et sur l'origine (FR-008), journalisé |

La session ouverte crée une `SsoSession` dont l'identifiant devient le claim `sid` des `id_token`
émis pendant sa durée de vie.

## Déconnexion

`POST /logout` ferme la session Laravel, marque la `SsoSession` révoquée et met en file la poussée de
déconnexion vers chaque participant (FR-034, FR-035). Une application peut aussi la déclencher en
renvoyant l'utilisateur sur cette route.

## Mot de passe oublié

`POST /password/forgot` répond **toujours** de la même façon, adresse connue ou non : répondre
autrement transformerait l'écran en oracle d'existence de compte. Le lien est à usage unique et à
durée limitée ; une demande plus récente invalide la précédente.

`POST /password/reset` applique l'exigence de robustesse (FR-009) et, au succès, ferme toutes les
autres sessions de l'utilisateur (FR-012) avec la poussée correspondante.

## Invitation

`GET /invitations/{token}` répond `410` si l'invitation est expirée ou déjà acceptée.
`POST /invitations/{token}` définit le mot de passe, fait passer le compte de `invited` à `active` et
ouvre la session dans la foulée.

## Ce qui ne passe pas par ces écrans

Le profil et le mot de passe restent également accessibles par `GET /me`, `PATCH /me` et
`PUT /me/password` ([admin-api.md](./admin-api.md)) : l'écran `/account` sert l'utilisateur devant son
navigateur, ces endpoints servent une application qui agit en son nom avec un `access_token`.
