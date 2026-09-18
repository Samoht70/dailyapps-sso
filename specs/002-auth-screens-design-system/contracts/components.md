# Contrat — composants Blade du parcours d'authentification

**Feature** : `002-auth-screens-design-system`

Le produit n'expose ici aucune interface machine : pas d'endpoint neuf, pas de charge utile,
pas de scope. La surface que cette feature publie est une **surface interne d'interface** —
les composants que les sept écrans composent, et que la feature 003 composera après eux.

C'est bien un contrat : FR-003 veut que ces contrôles soient définis une fois et réemployés
sans redéfinition. Un écran qui contourne un attribut au lieu de l'employer rompt ce contrat
même si la page s'affiche.

**Espace de noms** : `oidc`, servi par `loadViewsFrom()` dans `OidcServiceProvider`. Tout
composant s'appelle `<x-oidc::nom>`. Les fichiers vivent sous
`api/technical/oidc/resources/views/components/`.

**Règle transverse** : tout attribut non listé est fusionné sur l'élément racine du composant
via `$attributes->merge()`. Aucun composant n'accepte de texte en dur — les libellés reçus
viennent de `__('oidc::…')`, sans exception.

---

## `<x-oidc::layouts.screen>`

Coquille des six écrans d'entrée. Remplace la coquille actuelle, même nom de vue, donc aucune
retouche aux attributs `#[Layout]` des composants Livewire.

| Attribut | Type | Défaut | Rôle |
|---|---|---|---|
| `title` | `string` | `config('app.name')` | titre de l'onglet, déjà traduit |
| `headline` | `?string` | `screens.brand.headline` | accroche de l'aplat |
| `tagline` | `?string` | `screens.brand.tagline` | sous-titre de l'aplat |

Slot par défaut : le contenu de la colonne de droite, largeur utile 400 px, centré.

Sous 1024 px l'aplat disparaît et la marque se reporte au-dessus du contenu (D-009). La page
ne défile jamais horizontalement (FR-006).

---

## `<x-oidc::layouts.app>`

Coquille des pages connectées. Neuve.

| Attribut | Type | Défaut | Rôle |
|---|---|---|---|
| `title` | `string` | `config('app.name')` | titre de l'onglet |

La barre haute porte le logo sombre, l'adresse du compte authentifié et le formulaire de
déconnexion (`POST` vers `route('logout')`, jeton CSRF inclus). Elle lit `Auth::user()`
elle-même ; l'écran ne lui passe rien.

Slot par défaut : le contenu, centré, largeur utile 720 px.

---

## `<x-oidc::brand.logo>`

| Attribut | Type | Défaut | Valeurs |
|---|---|---|---|
| `tone` | `string` | `light` | `light` (fond sombre) · `dark` (fond clair) |
| `width` | `int` | `225` | largeur en px, hauteur déduite du rapport 225/32 |

Rend le SVG en ligne, sans requête réseau. Porte `role="img"` et un `aria-label` issu de
`screens.brand.logo_alt`.

---

## `<x-oidc::brand.panel>`

L'aplat noir. Consommé par `layouts.screen`, exposé pour que les écrans puissent en changer
l'accroche — l'invitation dit « Bienvenue chez nous. » plutôt que l'accroche par défaut.

| Attribut | Type | Défaut |
|---|---|---|
| `headline` | `string` | `screens.brand.headline` |
| `tagline` | `string` | `screens.brand.tagline` |

---

## `<x-oidc::heading>`

| Attribut | Type | Défaut | Valeurs |
|---|---|---|---|
| `level` | `int` | `1` | `1` (32/40 connecté, 24/32 en entrée) · `2` (20/28) · `3` (16/24) |

Rend `<h1>`, `<h2>` ou `<h3>` selon `level`, en `--font-display`. Slot : le libellé.

---

## `<x-oidc::card>`

Module blanc, rayon 16, ombre `--shadow-module`, gouttière interne 24 px.

| Attribut | Type | Défaut |
|---|---|---|
| `heading` | `?string` | `null` — titre de niveau 2, omis si absent |
| `hint` | `?string` | `null` — mention 12/16 sous le titre |

Slot : le contenu.

---

## `<x-oidc::field>`

Le composant central : un libellé, un champ, son message d'erreur. Aucun écran n'écrit un
`<input>` nu.

| Attribut | Type | Défaut | Rôle |
|---|---|---|---|
| `name` | `string` | — | **requis.** Nom du champ, et clé lue dans `$errors` |
| `label` | `string` | — | **requis.** Libellé traduit |
| `type` | `string` | `text` | `text` · `email` · `password` |
| `model` | `?string` | `$name` | propriété Livewire liée, via `wire:model` |
| `size` | `int` | `48` | `30` · `36` · `40` · `48` |
| `placeholder` | `?string` | `null` | aide, jamais l'étiquette du champ (D-002) |
| `hint` | `?string` | `null` | mention persistante sous le champ |
| `autocomplete` | `?string` | `null` | passé tel quel |
| `required` | `bool` | `false` | |
| `autofocus` | `bool` | `false` | |
| `disabled` | `bool` | `false` | |

Comportement imposé :

- l'`id` du champ vaut `name` ; le `<label for>` le vise ;
- une erreur présente pour `name` pose `aria-invalid="true"` sur le champ, `aria-describedby`
  vers le message, et rend celui-ci en `--color-error-text` avec `role="alert"` ;
- le champ ne dit jamais son erreur par la seule couleur — le message est toujours écrit
  (FR-007 et le fond du sujet : un contraste ne remplace pas une phrase).

---

## `<x-oidc::checkbox>`

| Attribut | Type | Défaut |
|---|---|---|
| `name` | `string` | — **requis** |
| `label` | `string` | — **requis** |
| `model` | `?string` | `$name` |

Zone cliquable d'au moins 24 px, libellé compris. Rayon `--radius-check`, coche en
`--color-brand` à l'état activé.

---

## `<x-oidc::button>`

| Attribut | Type | Défaut | Valeurs |
|---|---|---|---|
| `variant` | `string` | `primary` | `primary` (aplat rouge, texte blanc) · `outline` (bordure, texte encre) · `neutral` (gris) · `ghost` (texte seul) |
| `size` | `int` | `48` | `30` · `36` · `40` · `48` |
| `block` | `bool` | `false` | occupe toute la largeur |
| `type` | `string` | `submit` | `submit` · `button` |
| `href` | `?string` | `null` | rend un `<a>` au lieu d'un `<button>` |

Slot : le libellé. Anneau de focus visible en `--color-focus`, jamais supprimé.

---

## `<x-oidc::alert>`

Le bandeau de feedback. Porte les messages globaux — succès, échec d'authentification,
expiration.

| Attribut | Type | Défaut | Valeurs |
|---|---|---|---|
| `tone` | `string` | `info` | `success` · `error` · `warning` · `info` |
| `title` | `?string` | `null` | titre gras, omis si absent |

Slot : le corps du message.

Le rôle ARIA suit le ton : `role="alert"` pour `error` et `warning`, `role="status"` pour
`success` et `info`. Surface, bordure et texte viennent du trio du ton ; aucun écran ne
choisit une couleur.

---

## `<x-oidc::link>`

| Attribut | Type | Défaut | Rôle |
|---|---|---|---|
| `href` | `string` | — **requis** | |
| `icon` | `?string` | `null` | `chevron-left` — seule valeur admise, SVG en ligne |
| `navigate` | `bool` | `true` | pose `wire:navigate` |

Slot : le libellé.

---

## `<x-oidc::hint>`

Mention 12/16 en `--color-muted`. Aucun attribut ; slot : le texte.

---

## Ce que le contrat interdit

1. **Un écran ne déclare pas de classe de présentation sur un contrôle.** Une vue d'écran qui
   pose `class` sur un `<input>`, un `<button>` ou un `<label>` redéfinit ce que le socle
   définit — c'est ce que FR-003 et SC-001 refusent. Les classes de *disposition* sur les
   conteneurs de l'écran (`flex`, `gap-*`, `space-y-*`) restent à l'écran.
2. **Aucune valeur de couleur, de rayon ou de police en dur.** Tout passe par un token.
3. **Aucun libellé en dur.** Tout attribut de texte reçoit le retour d'un `__()`.
4. **Aucune hauteur de contrôle hors des quatre valeurs** 30 / 36 / 40 / 48.
5. **Aucun composant ne charge de ressource extérieure au produit** — ni police, ni image, ni
   feuille de style (FR-008, SC-006).
