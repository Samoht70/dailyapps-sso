# Contrat — réponses HTTP des sept écrans

**Feature** : `002-auth-screens-design-system`

Cette feature ne crée **aucune route** et n'en modifie **aucune**. Le tableau ci-dessous est
le contrat que la refonte ne doit pas bouger : il fige ce que le parcours répond aujourd'hui,
pour que ce qui change soit visiblement le corps de la réponse et rien d'autre.

`api/technical/oidc/routes/web.php` reste mot pour mot ce qu'il est.

---

## Réponses

| Route | Condition | Statut | Corps |
|---|---|---|---|
| `GET /login` | visiteur | 200 | écran de connexion |
| `GET /login` | déjà authentifié | 302 → `/account` | middleware `guest`, inchangé |
| `GET /password/forgot` | visiteur | 200 | écran de demande |
| `GET /password/reset/{token}` | jeton vivant, ou adresse absente de l'URL | 200 | formulaire |
| `GET /password/reset/{token}` | jeton mort **et** adresse présente | 200 | **état « lien expiré »** — neuf |
| `GET /invitations/{token}` | invitation en attente | 200 | formulaire d'activation |
| `GET /invitations/{token}` | périmée, consommée, ou jamais émise | **410** | **écran « invitation périmée »** — neuf |
| `GET /account` | authentifié | 200 | profil |
| `GET /account` | visiteur | 302 → `/login` | middleware `auth`, inchangé |
| `POST /logout` | authentifié | 302 | inchangé |

**Le 410 est un invariant, pas un détail.** Trois tests de `AcceptInvitationScreenTest`
l'affirment et SC-002 interdit d'y toucher. Ce qui change est le corps : une page d'erreur nue
devient un écran de marque portant une explication.

---

## Ce que les réponses ne disent pas

Contraintes de sécurité de la constitution, reconduites telles quelles. La refonte les hérite
et ne les affaiblit pas.

- **Aucune réponse ne révèle qu'un compte existe.** `oidc::auth.failed` est le même message
  pour une adresse inconnue et un mot de passe faux. L'écran de demande de lien répond
  `screens.forgot_password.sent` quoi qu'il arrive.
- **L'écran « lien expiré » n'est pas un oracle.** Une adresse inconnue portée par l'URL et un
  jeton faux donnent le même écran qu'un jeton réellement périmé.
- **L'écran « invitation périmée » ne nomme ni compte, ni organisation, ni administrateur.**
  Il oriente vers « l'administrateur de votre organisation » sans le désigner — il est servi
  à qui n'est pas authentifié.
- **Aucun secret, aucun jeton dans le corps d'une réponse.** Le jeton reste `#[Locked]` côté
  Livewire et n'est jamais rendu.
- **La temporisation ne bouge pas.** `ThrottleAuthentication` garde son comptage et son
  message ; le message change seulement d'endroit à l'écran (D-010).

---

## Emploi des traductions

Chaque écran ne rend que des clés `oidc::screens.*` et `oidc::auth.*`. Le contrat côté
traduction est celui du `data-model.md` : arborescences identiques entre `lang/fr` et
`lang/en`, messages d'invalidité réemployés sans retouche.

---

## Ce qui n'est pas livré

- `/oauth/authorize` et son écran de consentement : feature 003.
- La carte « Applications autorisées » du profil : feature 003.
- Le thème sombre du design system : hors périmètre déclaré de la spec.
- Le dépôt `mobile` : hors périmètre. Aucun commit ne doit y atterrir.
