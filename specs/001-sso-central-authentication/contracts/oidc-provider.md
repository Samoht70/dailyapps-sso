# Contrat — Surface OpenID Connect exposée aux applications

**Consommateurs** : les ~15 applications de l'écosystème. **Fournisseur** : `api`, couche
`technical/oidc`. Voir [research.md](../research.md) D1 à D5.

## Découverte

```
GET /.well-known/openid-configuration
```

Document de découverte OIDC, fourni par `jeremy379/laravel-openid-connect`. Il annonce au minimum
`issuer`, `authorization_endpoint`, `token_endpoint`, `userinfo_endpoint`, `jwks_uri`,
`scopes_supported`, `response_types_supported`, `code_challenge_methods_supported: ["S256"]`.

```
GET /oauth/jwks
```

Clés publiques de signature, avec `kid`. C'est par là qu'une application vérifie un `id_token` sans
appeler le point central.

## Flux d'identification

```
GET /oauth/authorize
    ?client_id=<slug du client>
    &redirect_uri=<parmi les URI déclarées>
    &response_type=code
    &scope=openid profile email applications
    &state=<aléa>
    &code_challenge=<S256>
    &code_challenge_method=S256
```

- Visiteur non identifié → redirection vers l'écran de connexion du front, l'URL visée conservée
  (FR-001, FR-003).
- `redirect_uri` absente des URI déclarées → **rejet sans redirection** (FR-006). L'utilisateur voit
  une erreur sur le point central ; il n'est jamais renvoyé vers l'adresse non déclarée.
- Client *first-party* → pas d'écran de consentement (D5).

```
POST /oauth/token
    grant_type=authorization_code | refresh_token
```

Réponse : `access_token` (JWT, 15 min), `refresh_token` (8 h glissantes, rotation à chaque usage),
`id_token`, `token_type`, `expires_in`.

Chaque `refresh_token` revalide l'état du compte, de l'organisation et de la licence. L'une des trois
est tombée → `invalid_grant`, et l'application doit renvoyer vers `/oauth/authorize`.

## Claims de l'`id_token`

| Claim | Portée | Contenu |
|-------|--------|---------|
| `sub` | toujours | identifiant stable de l'utilisateur |
| `sid` | toujours | identifiant de la session SSO — la clé de la poussée de déconnexion |
| `iss`, `aud`, `exp`, `iat`, `nonce` | toujours | standard OIDC |
| `name` | `profile` | |
| `email`, `email_verified` | `email` | |
| `organization` | `profile` | `{ id, name }` de l'organisation de rattachement |
| `roles` | `applications` | les clés des rôles détenus **sur l'application appelante uniquement** (FR-016, FR-017) |

Les claims sont composés par un fournisseur déclaré dans `functional/licensing` et branché sur le
point d'extension de `technical/oidc` — aucune application ne reçoit les droits d'une autre.

```
GET /oauth/userinfo
Authorization: Bearer <access_token>
```

Mêmes claims, filtrés par les scopes accordés.

## Erreurs d'accès

Réponses distinctes, parce que FR-018 et le scénario 5 de l'histoire 1 en dépendent :

| Situation | Réponse |
|-----------|---------|
| Identifiants invalides | reste sur l'écran de connexion, message identique que le compte existe ou non (FR-007) |
| Compte `disabled`, organisation `suspended` | `access_denied`, motif `account_unavailable` |
| Pas de licence valide | `access_denied`, motif `no_license` |
| Licence valide mais aucun accès attribué | `access_denied`, motif `no_access` |
| Trop de tentatives | `access_denied`, motif `throttled` (FR-008) |

## Poussée de déconnexion (back-channel logout)

Construite par nous (D3), absente des paquets. Le point central appelle l'URL déclarée par
l'application :

```
POST <application.backchannel_logout_url>
Content-Type: application/jwt

<logout_token signé, claims : iss, aud, iat, jti, sid, sub,
 events: { "http://schemas.openid.net/event/backchannel-logout": {} },
 reason: "logout" | "user_disabled" | "organization_suspended"
       | "license_revoked" | "password_changed">
```

**Ce que l'application doit faire** : vérifier la signature via le JWKS, fermer la session portant ce
`sid`, répondre `200` ou `204` sous 5 secondes.

**Ce que fait le point central** : job en file, réessais exponentiels, échec définitif journalisé en
`logout_push_failed`. Une application injoignable ne bloque pas les autres, et ne tient alors que par
l'expiration du jeton — c'est la limite assumée de SC-005.

## Ce qui n'est pas exposé

- `end_session_endpoint` (RP-initiated logout) : hors périmètre de cette feature. Une application
  déconnecte en renvoyant l'utilisateur sur `POST /logout` du point central, qui ferme la session et
  déclenche la poussée.
- Introspection : écartée (D3), elle ferait du point central un passage obligé à chaque requête.
- Grants `password`, `implicit`, `device` : désactivés. Seuls *authorization code* + PKCE et
  *client credentials* sont ouverts.
