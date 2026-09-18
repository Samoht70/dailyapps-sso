# Implementation Plan: Identité DailyApps sur le parcours d'authentification

**Branch**: `002-auth-screens-design-system` | **Date**: 2026-09-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-auth-screens-design-system/spec.md`

## Summary

Les cinq écrans d'authentification livrés par la feature 001 fonctionnent et sont testés,
mais n'appartiennent à personne : Tailwind brut, palette `gray-*`, classes d'`input`
recopiées d'un écran à l'autre. Cette feature leur donne l'identité DailyApps — celle du XEFI
Design System, déjà arbitrée — et ferme la seule impasse du parcours, le lien périmé.

L'approche tient en quatre mouvements :

1. **Transposer l'identité en tokens.** Les valeurs du design system deviennent un bloc
   `@theme` Tailwind v4 dans `technical/framework`, et les polices Lato et Montserrat sont
   téléchargées à la compilation par le plugin Vite déjà installé, donc servies par le
   produit (D-001, D-003, D-004).
2. **Écrire le socle de contrôles une fois.** Douze composants Blade anonymes dans la couche
   `oidc` — champ, bouton, case, bandeau, carte, coquilles. Le design system livre du React,
   inutilisable sous Livewire : ce sont ses valeurs et ses formes qu'on reprend, pas son code
   (D-008).
3. **Reposer les cinq écrans dessus**, sans toucher une ligne de leur logique. Aucune route ne
   bouge, aucun message ne change, aucun test n'est retouché.
4. **Ouvrir les deux écrans qui manquent** — lien de réinitialisation périmé, invitation
   périmée — en réemployant les libellés déjà traduits (D-006, D-007).

Les décisions et ce qu'elles écartent sont dans [research.md](./research.md).

## Affected Repos

<!-- speckit-multirepo:begin -->

| Repo | Rôle dans la feature |
|------|----------------------|
| api  | Livre la totalité de la feature : tokens, composants Blade, sept écrans, traductions, tests |

<!-- speckit-multirepo:end -->

`mobile` n'est pas touché : la spec le place hors périmètre et aucun commit ne doit y
atterrir.

## Technical Context

**Language/Version**: PHP 8.4

**Primary Dependencies**: Laravel 13.17, Livewire 4.4, Laravel Passport ; Tailwind CSS 4,
Vite 8, `laravel-vite-plugin` 3.1 (dont le module `fonts`, qui approvisionne les polices à la
compilation) ; `xefi/laravel-osdd` pour les couches. **Aucun paquet ajouté.**

**Storage**: sans objet — aucune migration, aucun modèle, aucune colonne. La feature habille
des écrans qui lisent des entités existantes.

**Testing**: PHPUnit, une seule suite, `./vendor/bin/sail test`. Les écrans Livewire se
testent par `Livewire::test(...)` et par requête HTTP, comme aujourd'hui.

**Target Platform**: navigateur, du téléphone au poste de travail ; serveur Linux, déployable
unique servi par Sail en développement.

**Project Type**: application web servie par un monolithe Laravel + Livewire, organisée en
couches OSDD.

**Performance Goals**: aucune ressource tierce sollicitée à l'affichage (FR-008) ; marque
rendue dans le même aller-retour que la page, le logo étant en SVG inline (D-005) ; aucune
régression du budget de latence que surveille `WatchLatencyBudget`.

**Constraints**: contraste minimum 4,5:1, ramené à 3:1 au-delà de 24 px (FR-007) ; aucun
défilement horizontal sur téléphone (FR-006) ; comportement des cinq écrans existants gelé
(FR-004) ; aucun test existant modifié (SC-002) ; le statut 410 de l'invitation périmée est
un invariant.

**Scale/Scope**: 7 écrans, 12 composants Blade, ~40 clés de traduction neuves en deux
langues, 1 dépôt, 1 couche métier touchée (`technical/oidc`) et 1 couche transverse
(`technical/framework`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution v1.0.0. Chaque principe confronté, et comment le plan s'y tient.

### I — Une seule source de vérité pour l'identité et les droits

**Confronté, non touché.** La feature ne crée ni annuaire, ni copie de droits, ni liste à
synchroniser. Les écrans lisent le point central lui-même ; le profil affiche l'utilisateur
authentifié, pas une projection. La carte « Applications autorisées » — la seule qui aurait
demandé de lire des accès — est explicitement reportée à la feature 003.

### II — Le raccordement passe par le standard, jamais par du sur-mesure

**Confronté, non touché.** Aucune route n'est créée ni modifiée ; `contracts/screens.md` fige
les réponses actuelles comme invariant. `/oauth/authorize` n'est pas dans le périmètre. Rien
ici n'ouvre de surface à une application cliente : les sept écrans sont l'interface humaine du
point central, pas une interface machine.

### III — Refus par défaut, et jamais sur un nom de rôle

**Confronté, non touché.** Les middlewares `guest` et `auth` restent posés à l'identique sur
les mêmes routes. Aucune vérification d'autorisation n'est ajoutée, donc aucune ne peut porter
sur un nom de rôle. Les deux écrans neufs sont servis à des visiteurs et ne nomment ni compte,
ni organisation, ni administrateur.

### IV — La révocation est immédiate et traçable

**Confronté, non touché.** Aucun chemin d'accès neuf : les deux écrans ajoutés sont des
états terminaux qui n'authentifient personne et n'ouvrent aucune session — il n'y a rien à
couper. `RecordAuthenticationEvents`, `OpenSsoSession` et le reste du journal de sécurité ne
sont pas modifiés ; l'habillage n'ajoute ni ne retire un événement.

### V — Le code vit en couches OSDD

**Confronté, tenu, avec deux points à instruire.**

Tout ce qui est logique de la feature atterrit dans une couche : composants, coquilles,
traductions, exception et tests dans `api/technical/oidc/` ; tokens de l'identité dans
`api/technical/framework/resources/css/theme.css`, parce que l'identité est de
l'infrastructure transverse et non un domaine — n'importe quelle couche qui servira un écran
s'en servira (D-003). Aucun `app/`, aucun `database/` ni `config/` racine n'est créé.

Deux fichiers racine sont modifiés, et ce ne sont pas des écarts :

- `api/resources/css/app.css` — une ligne d'`@import` vers le thème de la couche. Tailwind v4
  impose une entrée CSS unique ; le fichier existe déjà et ne portera aucune règle.
- `api/vite.config.js` — la déclaration des deux familles de polices. C'est un fichier de
  construction, au même titre que `package.json`, pas un endroit où vit une fonctionnalité.

`public/favicon.ico` est remplacé par le SVG de la tuile DailyApps : le favicon n'a pas
d'autre support possible que la racine publique (D-005).

Les réactions au cycle de vie passent toujours par des événements et des listeners déclarés
dans le provider ; aucun observer n'est introduit. La feature n'en ajoute d'ailleurs aucun.

### VI — Rien n'est livré sans test

**Confronté, tenu.** Les deux écrans neufs arrivent avec leurs tests dans
`api/technical/oidc/tests/Feature/`, dans la suite unique, sur des factories. Trois critères
de succès deviennent des tests plutôt que des intentions : SC-001 (aucun écran ne redéfinit un
contrôle), SC-004 (arborescences de traduction identiques entre `fr` et `en`), et le statut
410 de l'invitation périmée. Ce qui ne se teste pas — la ressemblance à la maquette, SC-005 —
est consigné comme vérification manuelle dans `quickstart.md`, nommé, pas passé sous silence.

SC-002 ajoute une porte que le vert seul ne donne pas : aucun fichier de test antérieur ne
doit apparaître comme modifié dans le diff. Le `quickstart.md` en donne la commande.

### Contraintes techniques et de sécurité

- **Stack** — Laravel + Livewire, déployable unique. Le plan écarte explicitement le montage
  de composants React du design system, qui réintroduirait le front que la feature 001 a
  retiré (D-008).
- **Paquets avant code** — aucun paquet ajouté, aucun retiré. Un écart est consigné au tableau
  de complexité : les contrôles Blade sont écrits à la main, faute d'un paquet arbitré qui les
  fournisse.
- **Base de données** — sans objet, aucune migration.
- **Secrets** — aucun secret, aucun jeton rendu. Le jeton de réinitialisation et celui
  d'invitation restent `#[Locked]`. Le message d'échec d'authentification ne change pas d'un
  caractère et ne révèle toujours pas si un compte existe ; l'écran « lien expiré » est
  construit pour ne pas devenir un oracle (D-007).
- **Interface** — aucun HTML dans une classe PHP : tout le balisage part en Blade, y compris
  le corps de la réponse 410, servi par une vue et non par une chaîne. Aucun texte en dur :
  les composants n'acceptent que des libellés déjà traduits, et le contrat le pose en règle.
- **Documentation** — rien créé hors de `specs/`. Aucun `docs/`, aucun fichier d'architecture.
  Le `CLAUDE.md` de `api` sera mis à jour — sa section « Status » dit encore « no feature
  implemented », ce qui est faux depuis la 001.
- **Commandes** — tout `artisan`, `composer` et test passe par `./vendor/bin/sail`. Seuls
  `npm` et `git` s'exécutent sur l'hôte.

### Workflow

Session ouverte à la racine du workspace. Tout chemin écrit commence par `api/`. Le
`CLAUDE.md` de `api` a été lu avant d'écrire ce plan. Branche coupée de `staging` par
`speckit.multirepo.branch`. Une seule merge request, sur `api` — la feature ne s'étend pas à
un second dépôt, donc pas d'ordre de fusion à arbitrer.

**Verdict : la porte passe.** Un écart, instruit ci-dessous.

### Ré-instruction après la phase 1

La conception a produit trois choses que la porte n'avait pas sous les yeux avant la phase 0,
et aucune ne la déplace :

- **Le contrat des composants** (`contracts/components.md`) pose en règle ce que le principe V
  et les contraintes d'interface demandaient : pas de libellé en dur, pas de couleur en dur,
  pas de contrôle redéfini par un écran. Une règle écrite est vérifiable ; c'est ce qui rend
  SC-001 testable plutôt que déclaratif.
- **Le contrat des écrans** (`contracts/screens.md`) fige les réponses HTTP actuelles au lieu
  d'en décrire de nouvelles. Il rend visible le seul endroit où la conception a dû arbitrer
  entre deux exigences de la spec — l'invitation périmée doit expliquer (FR-010) sans quitter
  son 410 (SC-002) — et l'arbitrage retenu ne touche que le corps de la réponse (D-006).
- **Le modèle** (`data-model.md`) confirme qu'aucune entité n'est introduite : ni migration,
  ni colonne, ni énumération de statut. Les contraintes de base de données de la constitution
  restent sans objet, et non pas contournées.

Un point mérite d'être nommé plutôt que tu : la conception ajoute au composant `ResetPassword`
une vérification au montage (D-007), ce qui touche un des cinq écrans que FR-004 gèle. Le gel
porte sur les validations, les redirections, les messages et les protections — tous inchangés.
Ce qui change est le moment où l'écran dit une invalidité qu'il disait déjà, et sans lui, FR-009
ne peut pas être tenu. Aucun test existant n'interroge cette route en HTTP ; les dix tests de
`PasswordResetTest` passent par `Livewire::test`, où le repli s'applique.

**Verdict après conception : la porte passe toujours.** L'écart reste unique et inchangé.

## Project Structure

### Documentation (this feature)

```text
specs/002-auth-screens-design-system/
├── plan.md              # Ce fichier
├── research.md          # Phase 0 — onze décisions et ce qu'elles écartent
├── data-model.md        # Phase 1 — tokens, composants, états d'écran
├── quickstart.md        # Phase 1 — comment prouver que c'est livré
├── contracts/
│   ├── components.md    # Le contrat des composants Blade
│   └── screens.md       # Les réponses HTTP, figées comme invariant
├── checklists/
└── tasks.md             # Phase 2 — produit par /speckit-tasks, pas par cette commande
```

### Source Code (repository root)

Un seul dépôt, `api`. Les chemins ci-dessous sont relatifs à la racine du workspace.

```text
api/
├── resources/css/app.css                       # MODIFIÉ — une ligne d'@import
├── vite.config.js                              # MODIFIÉ — Lato + Montserrat
├── public/favicon.ico                          # REMPLACÉ — tuile DailyApps
│
├── technical/framework/
│   └── resources/css/theme.css                 # NEUF — @theme : l'identité en tokens
│
└── technical/oidc/
    ├── resources/views/
    │   ├── components/
    │   │   ├── layouts/screen.blade.php        # REFONDU — aplat + colonne
    │   │   ├── layouts/app.blade.php           # NEUF — barre haute + contenu
    │   │   ├── brand/logo.blade.php            # NEUF — SVG inline, deux variantes
    │   │   ├── brand/panel.blade.php           # NEUF — l'aplat noir
    │   │   ├── heading.blade.php               # NEUF
    │   │   ├── card.blade.php                  # NEUF
    │   │   ├── field.blade.php                 # NEUF — libellé + champ + erreur
    │   │   ├── checkbox.blade.php              # NEUF
    │   │   ├── button.blade.php                # NEUF
    │   │   ├── alert.blade.php                 # NEUF
    │   │   ├── link.blade.php                  # NEUF
    │   │   └── hint.blade.php                  # NEUF
    │   └── livewire/
    │       ├── login.blade.php                 # REFONDU
    │       ├── forgot-password.blade.php       # REFONDU
    │       ├── reset-password.blade.php        # REFONDU + état « expiré »
    │       ├── accept-invitation.blade.php     # REFONDU
    │       ├── account.blade.php               # REFONDU — coquille app, cartes
    │       └── invitation-expired.blade.php    # NEUF — corps de la réponse 410
    │
    ├── src/
    │   ├── Exceptions/InvitationNoLongerValid.php   # NEUF — render() → vue, statut 410
    │   ├── Livewire/AcceptInvitation.php            # MODIFIÉ — lève l'exception
    │   ├── Livewire/ResetPassword.php               # MODIFIÉ — état $expired au mount
    │   └── Livewire/Account.php                     # MODIFIÉ — coquille app
    │
    ├── lang/{fr,en}/screens.php                # MODIFIÉ — clés neuves, deux langues
    │
    └── tests/Feature/
        ├── ExpiredLinkScreensTest.php          # NEUF — les deux écrans, statuts, messages
        ├── ScreenIdentityTest.php              # NEUF — SC-001 : aucun contrôle redéfini
        └── TranslationParityTest.php           # NEUF — SC-004 : fr et en alignés
```

**Structure Decision** : une seule couche métier touchée, `technical/oidc`, qui porte déjà les
cinq écrans, leurs routes, leurs traductions et leurs tests — et qui portera aussi la feature
003. L'identité seule remonte dans `technical/framework`, la couche transverse, parce qu'elle
n'appartient à aucun domaine. Les deux fichiers racine modifiés sont les points d'entrée
imposés par Tailwind et Vite ; ils importent et déclarent, ils ne décident rien.

Aucun fichier de test antérieur à la feature n'apparaît dans cette arborescence : c'est
l'invariant de SC-002, et il se lit ici.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Douze composants d'interface écrits à la main, alors que la constitution veut qu'un paquet passe avant du code | Le XEFI Design System, seule source arbitrée dans l'organisation, livre ses composants en **React** (`window.XEFIDesignSystem_1dd81f`). Aucun des paquets que nomme la constitution — lomkit, spatie, xefi/laravel-osdd — ne fournit de contrôle Blade. Il n'existe pas de paquet à préférer | **Monter le bundle React en îlots** : introduit un second runtime front, un pont vers Livewire à écrire et des champs que Livewire ne pilote plus — exactement le second front que la feature 001 a retiré, et que la constitution interdit sans amendement. **Prendre un paquet Blade tiers** (Flux, Mary, Filament Forms) : chacun apporte son identité, qu'il faudrait contredire token par token, et une dépendance à faire vivre — pour douze composants qu'on écrit une fois et que la feature 003 réemploie tels quels |
