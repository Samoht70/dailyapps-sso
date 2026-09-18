# Phase 1 — Modèle : tokens, composants, états d'écran

**Feature** : `002-auth-screens-design-system` | **Date** : 2026-09-18

**Cette feature n'introduit aucune entité persistée.** Pas de migration, pas de modèle
Eloquent, pas de colonne, pas d'énumération de statut. Elle habille des écrans qui lisent des
entités existantes — `User`, `Invitation`, `Organization` — sans en changer une seule.

Ce qui tient lieu de modèle ici, ce sont trois inventaires : les tokens que l'identité
définit, les composants qui les consomment, et les états que chaque écran peut prendre.

---

## 1. Tokens de l'identité

Déclarés une seule fois, dans `api/technical/framework/resources/css/theme.css`, sous
`@theme`. Les valeurs viennent du XEFI Design System (voir D-001 du `research.md`) ; la
colonne « nom Tailwind » est le nom sous lequel une classe utilitaire les atteint.

### Couleurs

| Nom Tailwind | Valeur | Emploi |
|---|---|---|
| `--color-brand` | `#e10600` | action primaire, marque |
| `--color-brand-hover` | `#cd0500` | survol de l'action primaire |
| `--color-brand-active` | `#a00400` | appui sur l'action primaire |
| `--color-ink` | `#000000` | aplat de marque |
| `--color-page` | `#f5f5f6` | fond de page connectée |
| `--color-surface` | `#ffffff` | carte, champ, barre haute |
| `--color-surface-subtle` | `#f2f2f2` | fond de contrôle désactivé |
| `--color-title` | `#2f2f2f` | titres |
| `--color-body` | `#3e3e3e` | texte courant |
| `--color-muted` | `#707070` | mentions, aides, placeholder (voir D-002) |
| `--color-disabled` | `#9f9f9f` | texte de contrôle désactivé |
| `--color-inverse` | `#ffffff` | texte sur l'aplat |
| `--color-inverse-muted` | `#9f9f9f` | accroche sur l'aplat |
| `--color-line` | `#d3d3d3` | bordures de champ et séparateurs |
| `--color-line-strong` | `#9f9f9f` | bordure de champ au survol |
| `--color-focus` | `#1473e6` | anneau de focus, liens |

### Tons de feedback

Quatre tons, trois valeurs chacun. Le ton porte le sens ; l'écran ne choisit pas ses couleurs.

| Ton | `--color-<ton>-surface` | `--color-<ton>-line` | `--color-<ton>-text` |
|---|---|---|---|
| `success` | `#e8f5e9` | `#a5d6a7` | `#317c34` |
| `error` | `#ffebee` | `#ef9a9a` | `#cb2d2d` |
| `warning` | `#fff8e1` | `#ffe082` | `#a85e00` |
| `info` | `#e3f2fd` | `#90caf9` | `#176dc1` |

### Typographie

| Nom Tailwind | Valeur |
|---|---|
| `--font-sans` | `Lato, system-ui, -apple-system, 'Segoe UI', sans-serif` |
| `--font-display` | `Montserrat, system-ui, 'Segoe UI', Arial, sans-serif` |

Échelle employée par les sept écrans — titre en `--font-display` gras, reste en `--font-sans` :

| Rôle | Taille / interligne | Graisse |
|---|---|---|
| H1 page connectée | 32 / 40 | 700 |
| H1 écran d'entrée | 24 / 32 | 700 |
| H2 carte | 20 / 28 | 700 |
| accroche de l'aplat | 32 / 40 | 700 |
| corps, libellé, bouton, champ | 14 / 20 | 400 |
| mention, aide, erreur | 12 / 16 | 400 |

### Formes et rythme

| Nom Tailwind | Valeur | Emploi |
|---|---|---|
| `--radius-field` | `8px` | champ, bouton, bandeau |
| `--radius-module` | `16px` | carte |
| `--radius-check` | `4px` | case à cocher |
| `--radius-pill` | `999px` | pastille |
| `--shadow-module` | `0 0 30px rgb(0 0 0 / .10)` | carte |
| `--spacing-*` | 4 / 8 / 12 / 16 / 24 / 32 / 48 px | l'échelle par défaut de Tailwind suffit |

Hauteurs de contrôle — quatre valeurs, aucune autre : **30** (xs), **36** (sm), **40** (md,
défaut des pages connectées), **48** (lg, défaut des écrans d'entrée).

---

## 2. Composants

Composants Blade anonymes de la couche `oidc`, sous
`api/technical/oidc/resources/views/components/`. Leur contrat détaillé — attributs, valeurs
admises, slots — est dans `contracts/components.md`.

| Composant | Rôle | Écrans servis |
|---|---|---|
| `layouts.screen` | coquille des écrans d'entrée : aplat + colonne | 1, 2, 3, 4, 6, 7 |
| `layouts.app` | coquille des pages connectées : barre haute + contenu | 5 |
| `brand.logo` | mot-symbole DailyApps en SVG, deux variantes | les 7 |
| `brand.panel` | aplat noir : logo, accroche, sous-titre | 1, 2, 3, 4, 6, 7 |
| `heading` | titre en `--font-display`, trois niveaux | les 7 |
| `card` | module blanc, rayon 16, ombre | 5 |
| `field` | libellé + champ + erreur, en un objet | 1, 3, 4, 5 |
| `checkbox` | case à cocher et son libellé | 1 |
| `button` | action, quatre variantes, quatre hauteurs | 1, 2, 3, 4, 5, 6 |
| `alert` | bandeau de feedback, quatre tons | 1, 2, 5, 6, 7 |
| `link` | lien de navigation, avec chevron optionnel | 1, 2, 6, 7 |
| `hint` | mention 12/16 en `--color-muted` | 1, 2, 4, 5, 7 |

**Règle** (FR-003, SC-001) : un écran compose ces composants et ne déclare aucune classe de
présentation pour un contrôle. Une vue d'écran qui écrit `class="… rounded-md border …"` sur
un `<input>` est un manquement, pas un raccourci.

---

## 3. Les sept écrans et leurs états

Aucun écran ne gagne de route. Les deux états neufs vivent dans les composants existants.

| # | Écran | Route | Composant | Coquille |
|---|---|---|---|---|
| 1 | Connexion | `GET /login` | `Login` | `screen` |
| 2 | Mot de passe oublié | `GET /password/forgot` | `ForgotPassword` | `screen` |
| 3 | Nouveau mot de passe | `GET /password/reset/{token}` | `ResetPassword` | `screen` |
| 4 | Invitation | `GET /invitations/{token}` | `AcceptInvitation` | `screen` |
| 5 | Profil | `GET /account` | `Account` | `app` |
| 6 | Lien de réinitialisation périmé | `GET /password/reset/{token}` | `ResetPassword`, état `expired` | `screen` |
| 7 | Invitation périmée | `GET /invitations/{token}` | vue `invitation-expired`, statut 410 | `screen` |

### États par écran

**1 — Connexion.** `vierge` · `erreur de validation` (sous le champ) · `échec
d'authentification` (bandeau `error`) · `verrouillé` (bandeau `error`, message de
temporisation). Les deux derniers peuvent coexister avec le premier (D-010).

**2 — Mot de passe oublié.** `formulaire` · `envoyé` (bandeau `success`, le formulaire
disparaît, lien de retour). Piloté par la propriété `$sent` existante.

**3 / 6 — Nouveau mot de passe.** `formulaire` · `erreur de validation` · `jeton refusé à la
soumission` (bandeau `error`) · **`expired`** — état neuf, décidé au `mount` quand l'adresse
accompagne le lien (D-007) : bandeau `warning`, bouton « Demander un nouveau lien »,
lien de retour. La propriété neuve est `public bool $expired = false`, `#[Locked]`.

**4 — Invitation.** `formulaire` · `erreur de validation` · `invitation consommée entre
l'affichage et l'envoi` (erreur sous le champ, comportement d'aujourd'hui).

**7 — Invitation périmée.** État neuf et terminal, atteint depuis `mount` : périmée, déjà
consommée, ou jamais émise — indistinguables et volontairement indistingués (D-006). Bandeau
`warning` portant `oidc::screens.invitation.expired`, orientation vers l'administrateur,
aucune action que l'utilisateur ne peut accomplir, lien de retour. **Statut HTTP 410.**

**5 — Profil.** `vierge` · `profil enregistré` (bandeau `success`) · `mot de passe changé`
(bandeau `success`) · `erreur de validation` par formulaire. Trois cartes prévues par la
maquette, **deux livrées** : « Informations » et « Changer de mot de passe ». « Applications
autorisées » relève de la feature 003 et n'est pas construite ici.

### Transitions

```
  login ──── mot de passe oublié ? ────► forgot ──── envoi ────► forgot (envoyé)
    ▲                                                                │
    │                                                          (courriel)
    │                                                                ▼
    ├──── succès ────► account                     reset ◄──── lien ouvert
    │                                                │
    │                                          jeton mort au mount
    │                                                ▼
    └──── « revenir à la connexion » ◄──── reset (expiré) ──► forgot

  invitation (courriel) ──► invitation ──── activation ────► account
                                 │
                           jeton mort au mount
                                 ▼
                     invitation périmée (410) ──► « revenir à la connexion »
```

---

## 4. Traductions

Le parcours ne parle que par `oidc::screens.*` et `oidc::auth.*`, en `fr` et en `en`
(`api/technical/oidc/lang/{fr,en}/`).

**Réemployées telles quelles**, aucune retouche (FR-011) :
`screens.reset_password.invalid`, `screens.invitation.expired`, et la totalité d'`auth.php`.

**Clés neuves**, chacune en français et en anglais (FR-005) :

| Groupe | Clés |
|---|---|
| `screens.brand` | `headline`, `tagline`, `invitation_headline`, `invitation_tagline`, `logo_alt` |
| `screens.link_expired` | `title`, `reset_heading`, `invitation_heading`, `request_new`, `ask_administrator`, `back` |
| `screens.login` | `error_title`, `email_placeholder`, `password_placeholder`, `support` |
| `screens.forgot_password` | `intro`, `sent_title`, `expiry_hint` |
| `screens.reset_password` | `email`, `password_placeholder`, `confirmation_placeholder` |
| `screens.invitation` | `password_placeholder`, `confirmation_placeholder`, `expired_hint` |
| `screens.account` | `info_heading`, `password_hint`, `saved_title`, `password_changed_title` |

`screens.reset_password.email` est neuve parce que l'écran 3 emprunte aujourd'hui le libellé
de l'écran 2 — un emprunt qui tient tant que les deux disent la même chose, et qui n'a pas à
survivre à une refonte.

**Invariant testable** (SC-004) : l'arborescence des clés de `lang/fr/screens.php` et celle de
`lang/en/screens.php` sont identiques. Même chose pour `auth.php`.
