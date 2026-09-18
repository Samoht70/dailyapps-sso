# Tasks: Identité DailyApps sur le parcours d'authentification

**Input**: Design documents from `/specs/002-auth-screens-design-system/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: inclus. La constitution (principe VI) interdit de livrer sans test, et le plan
nomme trois fichiers de test neufs qui portent SC-001, SC-002 et SC-004.

**Organization**: les tâches sont groupées par user story. La phase 2 est un socle bloquant :
les deux user stories composent les mêmes composants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallélisable (fichiers distincts, aucune dépendance en attente)
- **[Story]**: US1 ou US2
- Tout chemin part de la racine du workspace et commence par `api/`

## Conventions de dépôt

Dépôt unique : `api`. `mobile` n'est pas touché — aucun commit ne doit y atterrir.

Toute commande `artisan`, `composer` ou de test passe par `./vendor/bin/sail` depuis `api/`.
Seuls `npm` et `git` s'exécutent sur l'hôte.

---

## Phase 1: Setup (l'identité en tokens)

**Purpose**: poser les valeurs du design system et les polices, avant qu'un composant ne
s'en serve.

- [X] T001 [P] Créer `api/technical/framework/resources/css/theme.css` portant le bloc `@theme` de l'identité : les seize couleurs de `data-model.md` §1 (`--color-brand: #e10600`, `--color-brand-hover: #cd0500`, `--color-brand-active: #a00400`, `--color-ink: #000000`, `--color-page: #f5f5f6`, `--color-surface: #ffffff`, `--color-surface-subtle: #f2f2f2`, `--color-title: #2f2f2f`, `--color-body: #3e3e3e`, `--color-muted: #707070`, `--color-disabled: #9f9f9f`, `--color-inverse: #ffffff`, `--color-inverse-muted: #9f9f9f`, `--color-line: #d3d3d3`, `--color-line-strong: #9f9f9f`, `--color-focus: #1473e6`), les quatre tons de feedback en trio surface/line/text (`success` `#e8f5e9`/`#a5d6a7`/`#317c34`, `error` `#ffebee`/`#ef9a9a`/`#cb2d2d`, `warning` `#fff8e1`/`#ffe082`/`#a85e00`, `info` `#e3f2fd`/`#90caf9`/`#176dc1`), les deux familles (`--font-sans: Lato, system-ui, -apple-system, 'Segoe UI', sans-serif` et `--font-display: Montserrat, system-ui, 'Segoe UI', Arial, sans-serif`) et les formes (`--radius-field: 8px`, `--radius-module: 16px`, `--radius-check: 4px`, `--radius-pill: 999px`, `--shadow-module: 0 0 30px rgb(0 0 0 / .10)`). Le placeholder emploie `--color-muted` et non le `#8d8d8d` du design system, qui échoue le contraste à 3,32:1 (D-002)

- [X] T002 [P] Déclarer les polices dans `api/vite.config.js` : remplacer `bunny('Instrument Sans', { weights: [400, 500, 600] })` par `bunny('Lato', { weights: [300, 400, 700, 900] })` et `bunny('Montserrat', { weights: [700] })`. Le plugin approvisionne les fichiers pendant `vite build` et les sert depuis `public/build/assets/`, ce qui tient FR-008 (D-004)

- [X] T003 Remplacer le bloc `@theme` de `api/resources/css/app.css` — qui déclare encore `Instrument Sans` — par `@import '../../technical/framework/resources/css/theme.css';`. Le fichier ne porte plus aucune règle : il importe, il ne décide rien. Les directives `@source` existantes restent, celle sur `technical/*/resources/views` étant ce qui fait scanner les classes des composants de couche (dépend de T001)

- [X] T004 Lancer `npm run build` depuis `api/` et vérifier que `public/build/assets/` porte `lato-{300,400,700,900}-normal-*.woff2` et `montserrat-700-normal-*.woff2`. Si une graisse manque chez le fournisseur, appliquer le repli de D-004 : `.woff2` de Lato copiés du design system et Montserrat récupérée à la main, servies par le même chemin (dépend de T002, T003)

**Checkpoint**: les tokens sont atteignables par une classe utilitaire et les polices sont servies par le produit.

---

## Phase 2: Foundational (le socle de contrôles)

**Purpose**: écrire une fois les douze composants que les sept écrans composent. La feature
003 les réemploiera tels quels.

**⚠️ CRITICAL**: aucune user story ne peut commencer avant cette phase.

Le contrat de chaque composant — attributs, valeurs admises, défauts, comportement ARIA — est
dans `contracts/components.md` et fait foi. Règle transverse : tout attribut non listé est
fusionné par `$attributes->merge()`, et aucun composant n'accepte de texte en dur.

- [X] T005 Récupérer les trois SVG de marque depuis le XEFI Design System par identifiant d'asset — `logo-dailyapps-light.svg` (`a3374513b2295aaa194dcb3696c299fb`), `logo-dailyapps-dark.svg` (`75cd90371fbd81b37c9ac3acb91d4a2c`), `logo-tile-mark.svg` (`400078a88680641b7748a34de0a3dca6`) — la tuile carrée sans mot-symbole, retenue à l'implémentation contre `logo-tile-red-light.svg`, qui porte la signature « by XEFI » — et retirer de chacun la balise `<metadata>` portant le manifeste C2PA de 7,7 Ko. Les sources ne sont jamais redessinées. `viewBox="0 0 225 32"` pour le mot-symbole ; le SVG utile fait 8,2 Ko. Les trois fichiers nettoyés restent hors du dépôt à ce stade — ils sont consommés par T007 qui les inscrit dans `api/technical/oidc/resources/views/components/brand/logo.blade.php`, et par T017 pour la tuile

- [X] T006 [P] Ajouter le groupe `screens.brand` — `headline`, `tagline`, `invitation_headline`, `invitation_tagline`, `logo_alt` — dans `api/technical/oidc/lang/fr/screens.php` et `api/technical/oidc/lang/en/screens.php`, les deux arborescences identiques (FR-005)

- [X] T007 Créer `api/technical/oidc/resources/views/components/brand/logo.blade.php` : SVG en ligne, deux variantes par l'attribut `tone` (`light` pour fond sombre, `dark` pour fond clair, défaut `light`), attribut `width` en px avec un défaut de `225` et la hauteur déduite du rapport 225/32. Porte `role="img"` et un `aria-label` issu de `screens.brand.logo_alt`. Aucune requête réseau (dépend de T005, T006)

- [X] T008 Créer `api/technical/oidc/resources/views/components/brand/panel.blade.php` : l'aplat noir `--color-ink` portant le logo en variante claire, l'accroche en 32/40 gras `--font-display` sur `--color-inverse`, et le sous-titre sur `--color-inverse-muted`. Attributs `headline` et `tagline`, par défaut `screens.brand.headline` et `screens.brand.tagline` (dépend de T007)

- [X] T009 [P] Créer `api/technical/oidc/resources/views/components/heading.blade.php` : rend `<h1>`, `<h2>` ou `<h3>` selon l'attribut `level` (défaut `1`), en `--font-display` gras — 32/40 sur page connectée et 24/32 sur écran d'entrée pour le niveau 1, 20/28 pour le niveau 2, 16/24 pour le niveau 3

- [X] T010 [P] Créer `api/technical/oidc/resources/views/components/card.blade.php` : module `--color-surface`, rayon `--radius-module`, ombre `--shadow-module`, gouttière interne 24 px. Attributs `heading` et `hint`, tous deux `null` par défaut et omis si absents

- [X] T011 [P] Créer `api/technical/oidc/resources/views/components/field.blade.php` : libellé, champ et message d'erreur en un objet. Attributs `name` et `label` requis, `type` (`text` · `email` · `password`, défaut `text`), `model` (défaut `$name`, lié par `wire:model`), `size` (`30` · `36` · `40` · `48`, défaut `48`), `placeholder`, `hint`, `autocomplete`, `required`, `autofocus`, `disabled`. L'`id` du champ vaut `name` et le `<label for>` le vise ; une erreur présente pour `name` pose `aria-invalid="true"`, un `aria-describedby` vers le message, et rend celui-ci en `--color-error-text` avec `role="alert"`. L'erreur est toujours écrite, jamais portée par la seule couleur

- [X] T012 [P] Créer `api/technical/oidc/resources/views/components/checkbox.blade.php` : attributs `name` et `label` requis, `model` (défaut `$name`). Zone cliquable d'au moins 24 px libellé compris, rayon `--radius-check`, coche en `--color-brand` à l'état activé

- [X] T013 [P] Créer `api/technical/oidc/resources/views/components/button.blade.php` : attribut `variant` (`primary` aplat `--color-brand` texte blanc · `outline` bordure texte encre · `neutral` gris · `ghost` texte seul, défaut `primary`), `size` (`30` · `36` · `40` · `48`, défaut `48`), `block`, `type` (`submit` · `button`, défaut `submit`), `href` qui rend un `<a>` au lieu d'un `<button>`. Anneau de focus visible en `--color-focus`, jamais supprimé

- [X] T014 [P] Créer `api/technical/oidc/resources/views/components/alert.blade.php` : attribut `tone` (`success` · `error` · `warning` · `info`, défaut `info`) et `title` optionnel. Surface, bordure et texte viennent du trio du ton ; aucun écran ne choisit une couleur. Le rôle ARIA suit le ton — `role="alert"` pour `error` et `warning`, `role="status"` pour `success` et `info`

- [X] T015 [P] Créer `api/technical/oidc/resources/views/components/link.blade.php` : attribut `href` requis, `icon` dont `chevron-left` est la seule valeur admise et se rend en SVG inline, `navigate` (défaut `true`) qui pose `wire:navigate`

- [X] T016 [P] Créer `api/technical/oidc/resources/views/components/hint.blade.php` : mention 12/16 en `--color-muted`. Aucun attribut, un slot

- [X] T017 Remplacer `api/public/favicon.ico` par la tuile DailyApps issue de T005, et poser la balise `<link rel="icon">` correspondante dans les deux coquilles. C'est le seul endroit du parcours où un fichier public reste le bon support (D-005) (dépend de T005)

- [X] T018 Refondre `api/technical/oidc/resources/views/components/layouts/screen.blade.php` — même nom de vue, donc aucun `#[Layout]` à retoucher. Aplat de marque à gauche par `<x-oidc::brand.panel>`, colonne de contenu à droite de 400 px de largeur utile, centrée. Attributs `title` (défaut `config('app.name')`), `headline` et `tagline` passés à l'aplat. Sous 1024 px l'aplat disparaît et la marque se reporte au-dessus du contenu ; la page ne défile jamais horizontalement (D-009, FR-006) (dépend de T008)

- [X] T019 Créer `api/technical/oidc/resources/views/components/layouts/app.blade.php` : coquille des pages connectées. Barre haute portant le logo en variante sombre, l'adresse du compte authentifié lue par la coquille elle-même via `Auth::user()`, et le formulaire de déconnexion en `POST` vers `route('logout')` avec jeton CSRF. Slot centré, largeur utile 720 px. Attribut `title` (défaut `config('app.name')`) (dépend de T007)

**Checkpoint**: le socle est complet. Les deux user stories peuvent partir.

---

## Phase 3: User Story 1 - Un parcours d'authentification qui porte la marque (Priority: P1) 🎯 MVP

**Goal**: les cinq écrans existants partagent palette, typographie et contrôles, portent la
marque, et leur comportement ne bouge pas d'un caractère.

**Independent Test**: parcourir les cinq écrans, vérifier qu'ils partagent l'identité et que
validations, redirections et messages sont strictement inchangés.

- [X] T020 [US1] Ajouter dans `api/technical/oidc/lang/fr/screens.php` et `api/technical/oidc/lang/en/screens.php` les clés neuves des cinq écrans, arborescences identiques : `login.error_title`, `login.email_placeholder`, `login.password_placeholder`, `login.support` ; `forgot_password.intro`, `forgot_password.sent_title`, `forgot_password.expiry_hint` ; `reset_password.email`, `reset_password.password_placeholder`, `reset_password.confirmation_placeholder` ; `invitation.password_placeholder`, `invitation.confirmation_placeholder`, `invitation.expired_hint` ; `account.info_heading`, `account.password_hint`, `account.saved_title`, `account.password_changed_title`. `reset_password.email` est neuve parce que l'écran emprunte aujourd'hui le libellé de l'écran de demande. Aucune clé existante n'est retouchée (FR-011)

- [X] T021 [US1] Refondre `api/technical/oidc/resources/views/livewire/login.blade.php` sur les composants du socle. La vue lit `$errors` et répartit : si le message porté par la clé `email` est l'un des messages d'`oidc::auth.*`, il monte dans un `<x-oidc::alert tone="error">` en haut du formulaire ; sinon il reste sous le champ. `Login::fail()` n'est pas touché — il accroche toujours à `email` via `addError`, ce que `LoginScreenTest` vérifie (D-010, FR-004)

- [X] T022 [P] [US1] Refondre `api/technical/oidc/resources/views/livewire/forgot-password.blade.php` : état `formulaire` et état `envoyé` piloté par la propriété `$sent` existante — bandeau `success`, formulaire retiré, lien de retour

- [X] T023 [P] [US1] Refondre `api/technical/oidc/resources/views/livewire/reset-password.blade.php` sur les composants du socle, états `formulaire`, `erreur de validation` et `jeton refusé à la soumission` en bandeau `error`. L'état `expired` arrive en phase 4

- [X] T024 [P] [US1] Refondre `api/technical/oidc/resources/views/livewire/accept-invitation.blade.php` sur les composants du socle. L'aplat porte `screens.brand.invitation_headline` et `screens.brand.invitation_tagline` plutôt que l'accroche par défaut

- [X] T025 [US1] Basculer `api/technical/oidc/src/Livewire/Account.php` sur `#[Layout('oidc::components.layouts.app')]`. Aucune autre ligne de la classe ne bouge (dépend de T019)

- [X] T026 [US1] Refondre `api/technical/oidc/resources/views/livewire/account.blade.php` en deux `<x-oidc::card>` — « Informations » et « Changer de mot de passe » —, chacune avec ses états de succès en bandeau. La carte « Applications autorisées » de la maquette n'est **pas** construite : elle relève de la feature 003 (dépend de T025)

- [X] T027 [US1] Créer `api/technical/oidc/tests/Feature/ScreenIdentityTest.php` : porte SC-001. Vérifie qu'aucune vue de `resources/views/livewire/` ne porte de balise `<input>`, `<button>`, `<label>`, `<select>` ou `<textarea>` brute, et qu'aucune vue de `resources/views/` hors `components/brand/` ne porte de valeur de couleur littérale (`#rrggbb` ou `rgb(`). Vérifie aussi que chaque écran monte la coquille attendue et porte la marque

- [X] T028 [US1] Créer `api/technical/oidc/tests/Feature/TranslationParityTest.php` : porte SC-004. Aplatit les arborescences de `lang/fr/screens.php` et `lang/en/screens.php` et affirme qu'elles sont identiques. Même contrôle sur `auth.php`

- [X] T029 [US1] Lancer `./vendor/bin/sail test` depuis `api/`. Tout au vert, y compris les dix tests de `PasswordResetTest`, les huit d'`AcceptInvitationScreenTest`, ceux de `LoginScreenTest`, d'`AccountScreenTest` et de `LayerViewsTest` — dont `it_resolves_the_layer_view_namespace`, qui affirme l'existence de `oidc::components.layouts.screen`

- [X] T030 [US1] Porte SC-002 : `git -C api diff --stat staging -- 'technical/oidc/tests/**' 'functional/**/tests/**'` ne montre que des fichiers neufs. Une seule ligne de modification sur un test antérieur fait échouer le critère, quel que soit l'état du vert

**Checkpoint**: les cinq écrans portent l'identité, la suite est verte, aucun test n'a été accommodé.

---

## Phase 4: User Story 2 - Une sortie de secours quand le lien n'est plus valable (Priority: P2)

**Goal**: un lien de réinitialisation périmé et une invitation périmée expliquent ce qui s'est
passé et donnent la suite — action directe quand elle est en son pouvoir, interlocuteur sinon.

**Independent Test**: ouvrir un lien de réinitialisation périmé puis une invitation périmée,
et vérifier que chaque cas affiche son propre message et sa propre action.

- [X] T031 [US2] Ajouter le groupe `screens.link_expired` — `title`, `reset_heading`, `invitation_heading`, `request_new`, `ask_administrator`, `back` — dans `api/technical/oidc/lang/fr/screens.php` et `api/technical/oidc/lang/en/screens.php`. Les messages d'invalidité eux-mêmes, `screens.reset_password.invalid` et `screens.invitation.expired`, sont réemployés sans retouche (FR-011)

- [X] T032 [US2] Créer `api/technical/oidc/src/Exceptions/InvitationNoLongerValid.php` : exception dédiée dont `render()` renvoie la vue de la couche avec le statut **410**. Aucun HTML dans la classe — le corps part en Blade

- [X] T033 [US2] Créer `api/technical/oidc/resources/views/livewire/invitation-expired.blade.php` : corps de la réponse 410, monté sur `layouts.screen`. Bandeau `warning` portant `oidc::screens.invitation.expired`, orientation vers l'administrateur de l'organisation, lien de retour vers la connexion, et **aucun bouton d'action** — rien que l'utilisateur ne puisse accomplir. L'écran ne nomme ni compte, ni organisation, ni administrateur : il est servi à qui n'est pas authentifié (FR-010, dépend de T031)

- [X] T034 [US2] Modifier `api/technical/oidc/src/Livewire/AcceptInvitation.php` : `mount` lève `InvitationNoLongerValid` au lieu d'`abort_if($invitation === null, 410)`. Le statut ne bouge pas — trois tests d'`AcceptInvitationScreenTest` l'affirment et SC-002 interdit d'y toucher. Périmée, déjà consommée et jamais émise restent indistinguables, et le restent volontairement : les distinguer serait un oracle (D-006, dépend de T032, T033)

- [X] T035 [US2] Modifier `api/technical/oidc/src/Livewire/ResetPassword.php` : ajouter `public bool $expired = false;` en `#[Locked]`, et vérifier dans `mount` — lorsque l'adresse accompagne le lien — le jeton par `Password::broker()->getRepository()->exists($user, $token)`, qui lit sans consommer. Sans adresse dans l'URL, l'écran se comporte comme aujourd'hui : c'est le repli que prennent les dix tests de `PasswordResetTest`, qui passent par `Livewire::test`. Le contrôle à la soumission reste en place et reste le gardien. Une adresse inconnue et un jeton faux donnent le même écran qu'un jeton réellement périmé (D-007)

- [X] T036 [US2] Ajouter l'état `expired` à `api/technical/oidc/resources/views/livewire/reset-password.blade.php` : bandeau `warning` portant `oidc::screens.reset_password.invalid`, bouton « Demander un nouveau lien » vers `password.forgot`, lien de retour. Statut 200 — une page d'erreur qui propose un bouton serait un contresens (dépend de T035)

- [X] T037 [US2] Créer `api/technical/oidc/tests/Feature/ExpiredLinkScreensTest.php` : l'invitation périmée répond **410** et son corps porte `oidc::screens.invitation.expired` ; l'état « lien de réinitialisation expiré » répond **200**, porte `oidc::screens.reset_password.invalid` et une action vers `password.forgot` ; un lien sans adresse dans l'URL rend toujours le formulaire. Sur factories, dans la suite unique

- [X] T038 [US2] Relancer `./vendor/bin/sail test` depuis `api/` et reprendre le contrôle de T030 — aucun test antérieur modifié

**Checkpoint**: les deux impasses sont fermées, les sept écrans répondent.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T039 [P] Lancer `cd api && vendor/bin/pint --dirty --format agent`

- [X] T040 Porte SC-006 : `npm run build` depuis `api/`, puis vérifier qu'aucune URL tierce ne subsiste — `grep -rnE 'https?://(fonts\.|cdn\.|[a-z0-9.-]*googleapis|bunny\.net)' public/build/ resources/ technical/*/resources/` ne doit rien sortir. Les `@font-face` du paquet pointent vers `public/build/assets/*.woff2`

- [X] T041 [P] Mettre à jour la section « Status » de `api/CLAUDE.md`, qui dit encore « no feature implemented » — faux depuis la feature 001

- [ ] T042 Vérifications manuelles du `quickstart.md` §6, celles qu'aucun test ne porte : les sept écrans à 375 px sans défilement horizontal, la navigation au clavier seul avec anneau de focus visible partout, la ressemblance à la maquette, et SC-005 — quelqu'un placé devant `/login` et devant une capture de l'écran d'avant doit reconnaître le vrai immédiatement

- [X] T043 Depuis la racine du workspace, `/speckit-multirepo-status`. Attendu : `api` sur `002-auth-screens-design-system`, rien de non commité, rien de non poussé ; `mobile` sur `staging`, intact. Le rapport se prend au pied de la lettre

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: aucune dépendance
- **Foundational (Phase 2)**: dépend de la phase 1 — BLOQUE les deux user stories
- **User Story 1 (Phase 3)**: dépend de la phase 2
- **User Story 2 (Phase 4)**: dépend de la phase 2. Indépendante d'US1 sur le fond, mais T036 touche la vue que T023 refond — à séquencer si les deux stories sont menées en parallèle
- **Polish (Phase 5)**: dépend des deux user stories

### User Story Dependencies

- **US1 (P1)**: part dès la phase 2 finie. Aucune dépendance sur US2
- **US2 (P2)**: part dès la phase 2 finie. Un seul point de contact avec US1 — `reset-password.blade.php`, refondue en T023 et complétée en T036

### Parallel Opportunities

- T001 et T002 ensemble ; T003 puis T004 suivent
- T009 à T016 — huit composants, huit fichiers, aucune dépendance entre eux
- T006 pendant T005
- T022, T023 et T024 ensemble, une fois T020 posée
- T039 et T041 ensemble

---

## Parallel Example: Phase 2

```bash
# Les huit composants sans dépendance, ensemble :
Task: "Créer components/heading.blade.php"
Task: "Créer components/card.blade.php"
Task: "Créer components/field.blade.php"
Task: "Créer components/checkbox.blade.php"
Task: "Créer components/button.blade.php"
Task: "Créer components/alert.blade.php"
Task: "Créer components/link.blade.php"
Task: "Créer components/hint.blade.php"
```

---

## Implementation Strategy

### MVP (User Story 1 seule)

1. Phase 1 — les tokens et les polices
2. Phase 2 — le socle, bloquant
3. Phase 3 — les cinq écrans reposés dessus
4. **STOP et VALIDER** : la suite verte, aucun test antérieur modifié, les cinq écrans à l'œil
5. Livrable en l'état — le parcours porte la marque, les impasses restent ce qu'elles sont

### Livraison incrémentale

1. Phases 1 et 2 → le socle est prêt, rien n'est visible
2. + US1 → le parcours porte la marque (MVP)
3. + US2 → les deux impasses sont fermées
4. Phase 5 → les portes qui ne se testent pas en PHPUnit

---

## Notes

- Un commit par tâche. Convention de commit du dépôt `api` — lire son `CLAUDE.md` avant de committer
- `mobile` n'est pas touché : la spec le place hors périmètre
- Aucun paquet ajouté ni retiré, aucune migration, aucun modèle
- Aucun fichier de test antérieur à la feature n'apparaît comme modifié — c'est SC-002, et T030 comme T038 en font une porte
- Aucun texte en dur nulle part : tout libellé vient de `__('oidc::…')` et existe en français et en anglais
