# Contrat — API de gouvernance et de droits

**Consommateurs** : l'application d'administration / portail (dépôt distinct, hors périmètre) et le
front du point central. **Fournisseur** : `api`.

CRUD via `lomkit/laravel-rest-api`, le reste en contrôleurs (D8). URIs au pluriel, imbrication d'un
niveau au plus (`laravel:api-routing`). Authentification par `access_token` OIDC ; le périmètre de
lecture et d'écriture vient des `Control` de `lomkit/laravel-access-control`, jamais d'un test sur un
nom de rôle.

## Ressources REST

| Ressource | URI | Qui peut quoi |
|-----------|-----|---------------|
| Organisations | `/organizations` | exploitant : tout. Administrateur client : lire la sienne |
| Utilisateurs | `/users` | exploitant : tout. Administrateur client : sa seule organisation (FR-028) |
| Applications | `/applications` | exploitant : tout. Autres : lecture des `published` |
| Rôles applicatifs | `/applications/{id}/roles`, `/application-roles/{id}` | exploitant : tout |
| Licences | `/organizations/{id}/licenses`, `/licenses/{id}` | exploitant : tout. Administrateur client : lire les siennes |
| Accès | `/users/{id}/application-accesses`, `/application-accesses/{id}` | administrateur client : dans son organisation et dans la limite de ses licences |
| Événements de sécurité | `/security-events` | lecture seule, périmètre de l'appelant (FR-038) |

Chaque ressource suit l'enveloppe `search` / `mutate` de `lomkit/laravel-rest-api`. Aucun contrôleur
CRUD écrit à la main.

**Règles appliquées côté serveur, pas côté client** :

- Attribuer un accès vérifie la licence valide et le siège disponible, sous verrou (FR-024, D11).
- Retirer le dernier administrateur actif d'une organisation est refusé (FR-029).
- Inviter une adresse déjà rattachée est refusé, explicitement (FR-026).
- Attribuer un rôle d'une autre application est refusé.
- Toute écriture produit un `SecurityEvent` (FR-037).

## Endpoints non-CRUD

```
GET /me/applications
```

FR-014, FR-015. Les applications que l'appelant identifié peut atteindre, avec `slug`, `name`,
`logo_url`, `home_url`. Croise licence valide, accès attribué, état du compte et état de
l'organisation. Liste vide = `200` avec `data: []`, jamais une erreur (FR-018).

C'est l'endpoint que le portail consomme. Il n'est pas un CRUD : sa réponse est le résultat d'une
question, pas la projection d'une table.

```
GET  /me
PATCH /me
PUT  /me/password
```

FR-013. Profil et mot de passe de l'appelant. Le changement de mot de passe ferme toutes ses sessions
(FR-012) et déclenche la poussée de déconnexion.

```
POST   /applications/{id}/client-secret     rotation, secret renvoyé une seule fois
DELETE /applications/{id}/client-secret     révocation
POST   /applications/{id}/publish
POST   /applications/{id}/retire
POST   /organizations/{id}/suspend
POST   /organizations/{id}/activate
POST   /users/{id}/disable
POST   /users/{id}/enable
POST   /users/{id}/resend-invitation
```

FR-033, FR-020, FR-021, FR-027, FR-032. Ce sont des transitions d'état, pas des mises à jour de
champ : les exposer comme des actions nommées rend les transitions illégales impossibles à déclencher
par un `PATCH status`.

## Codes de réponse

| Code | Quand |
|------|-------|
| `200` / `201` | succès |
| `401` | jeton absent, expiré ou révoqué |
| `403` | hors périmètre — autre organisation, permission manquante |
| `409` | règle métier violée : sièges épuisés, dernier administrateur, adresse déjà rattachée, transition illégale |
| `422` | validation d'entrée |
| `429` | limitation de débit |

Le `409` porte un code machine (`seats_exhausted`, `last_admin`, `email_already_attached`,
`illegal_transition`) pour que l'appelant sache quoi dire à l'utilisateur, plutôt qu'un message à
analyser.
