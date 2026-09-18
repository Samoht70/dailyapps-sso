# Phase 0 — Recherche : identité DailyApps sur le parcours d'authentification

**Feature** : `002-auth-screens-design-system` | **Date** : 2026-09-18

Le `Technical Context` du plan ne portait aucun `NEEDS CLARIFICATION` sur la stack — elle
est arrêtée par la constitution et lisible dans `api/composer.json`. Les inconnues étaient
ailleurs : où loger une identité visuelle dans une architecture en couches, comment servir
des polices sans service extérieur, et comment ouvrir deux écrans neufs sans casser les
tests qui gardent les cinq existants.

---

## D-001 — Les valeurs de l'identité sont lues, pas inventées

**Décision** : reprendre telles quelles les valeurs du XEFI Design System, lues dans
`tokens.css` de la maquette (`project/ds/xefidesignsystem_1dd81f/tokens.css`), et ne
transposer que ce que les sept écrans emploient.

Le socle retenu :

| Rôle | Token DS | Valeur |
|------|----------|--------|
| Marque | `--primary` / `--xefi-red` | `#e10600` |
| Aplat de marque | `--xefi-black` | `#000000` |
| Fond de page | `--background` | `#f5f5f6` |
| Surface de carte | `--surface-card` | `#ffffff` |
| Titre | `--text-title` / `--grey-900` | `#2f2f2f` |
| Corps | `--text-body` / `--grey-800` | `#3e3e3e` |
| Mention | `--text-muted` / `--grey-500` | `#707070` |
| Bordure | `--border-subtle` / `--grey-100` | `#d3d3d3` |
| Lien | `--link` | `#1473e6` |
| Rayons | `--radius-field` / `--radius-module` / `--radius-pill` | 8 / 16 / 999 px |
| Ombre de module | `--shadow-module` | `0 0 30px rgba(0,0,0,.10)` |
| Espacements | `--space-xs…3xl` | 4 / 8 / 12 / 16 / 24 / 32 / 48 px |
| Hauteurs de contrôle | XS / S / M / L | 30 / 36 / 40 / 48 px |

Feedback, quatre tons, chacun surface + bordure + texte :

| Ton | Surface | Texte |
|-----|---------|-------|
| succès | `rgb(232,245,233)` | `#317c34` |
| erreur | `rgb(255,235,238)` | `#cb2d2d` |
| alerte | `rgb(255,248,225)` | `#a85e00` |
| information | `rgb(227,242,253)` | `#176dc1` |

**Rationale** : l'hypothèse de la spec est que l'identité est déjà arbitrée. Recopier les
valeurs plutôt que les rapprocher à l'œil est la seule manière de tenir SC-001 sur la durée.

**Alternatives écartées** : charger `tokens.css` en entier (29 Ko, dont un thème sombre hors
périmètre, une grille de données et une centaine de couleurs DailyUp qu'aucun écran
n'emploie) ; approximer la palette en classes Tailwind natives (`red-600`, `gray-*`), qui
donne un rouge voisin mais faux et rouvre la question à chaque écran.

---

## D-002 — Le rouge de marque passe le contraste, le gris de placeholder non

**Décision** : les couples du DS sont retenus tels quels, **sauf le texte de placeholder**,
qui passe de `--text-placeholder` (`#8d8d8d`) à `--text-muted` (`#707070`).

Ratios calculés (WCAG 2.1, formule de luminance relative) :

| Couple | Ratio | Verdict |
|--------|-------|---------|
| blanc sur `#e10600` (bouton primaire) | 4,97:1 | conforme |
| `#1473e6` sur blanc (lien) | 4,54:1 | conforme |
| `#3e3e3e` sur blanc (corps) | 10,70:1 | conforme |
| `#707070` sur blanc (mention) | 4,95:1 | conforme |
| `#707070` sur `#f5f5f6` (mention sur page) | 4,55:1 | conforme |
| `#2f2f2f` sur `#f5f5f6` (titre) | 12,29:1 | conforme |
| `#9f9f9f` sur noir (accroche de l'aplat) | 7,93:1 | conforme |
| succès / erreur / alerte / information sur leur surface | 4,59 à 4,65:1 | conforme |
| **`#8d8d8d` sur blanc (placeholder DS)** | **3,32:1** | **échoue** |

**Rationale** : FR-007 ne distingue pas le texte de placeholder du reste. Le DS le place à
3,32:1, ce qui conviendrait à un texte de 24 px et pas à un champ de formulaire. Le seul
token qui corrige sans quitter la palette est `--text-muted`, déjà présent.

**Alternatives écartées** : renoncer aux placeholders — la maquette s'en sert pour porter
une contrainte utile (« 12 caractères minimum ») ; inventer un gris intermédiaire, qui
ajoute une valeur hors DS pour un problème que le DS résout déjà.

Conséquence pour l'implémentation : aucun placeholder ne porte d'information que le libellé
ne porte pas — le placeholder reste une aide, jamais l'étiquette du champ.

---

## D-003 — Les tokens vivent dans `technical/framework`, les composants dans `technical/oidc`

**Décision** : `@theme` part dans `api/technical/framework/resources/css/theme.css`, importé
par `api/resources/css/app.css`. Les composants Blade partent dans
`api/technical/oidc/resources/views/components/`.

**Rationale** : la constitution (principe V) interdit qu'une fonctionnalité vive hors d'une
couche. Deux natures distinctes, deux couches :

- l'identité — palette, typographie, rayons — est de l'infrastructure transverse : n'importe
  quelle couche qui servira un écran demain s'en sert. `technical/framework` porte déjà ce
  qui est transverse et sans domaine (handler d'exceptions, sessions, cache) ;
- les contrôles et les coquilles du parcours d'authentification sont à `technical/oidc`, qui
  porte déjà les cinq écrans, leurs routes, leurs traductions et leurs tests. La feature 003,
  qui réemploiera ce socle, est elle aussi une feature oidc.

`api/resources/css/app.css` et `api/vite.config.js` restent modifiés : ce sont les points
d'entrée que Tailwind v4 et Vite imposent à la racine, au même titre que `package.json`. Ils
ne portent aucune règle — l'un importe, l'autre déclare les polices.

**Vérifié** : Tailwind v4 lit un bloc `@theme` dans un fichier atteint par `@import` depuis
l'entrée ; `app.css` importe déjà hors de son dossier et déclare `@source` sur
`technical/*/resources/views`, donc les classes des composants de couche sont scannées.

**Alternatives écartées** : ouvrir une couche `technical/design` pour un fichier CSS et une
douzaine de composants — un provider, un `composer.json` et une suite de tests pour ça, sans
un second consommateur pour le justifier ; loger `@theme` directement dans `app.css`, ce qui
met l'identité hors couche.

---

## D-004 — Les polices sont téléchargées à la compilation, pas au chargement de la page

**Décision** : remplacer `bunny('Instrument Sans')` par `bunny('Lato', { weights: [300, 400,
700, 900] })` et `bunny('Montserrat', { weights: [700] })` dans `api/vite.config.js`.

**Rationale** : FR-008 interdit de dépendre d'un service extérieur *au moment où l'écran
s'affiche*. Le plugin `laravel-vite-plugin/fonts` résout exactement cela : il va chercher les
fichiers chez le fournisseur **pendant `vite build`**, les écrit dans `public/build/assets/`
et génère un `@font-face` qui pointe vers ces copies. Le dépôt en porte déjà la preuve —
`public/build/assets/instrument-sans-400-normal-*.woff2` et `fonts-manifest.json` viennent de
ce mécanisme. Aucune requête ne part vers un tiers à l'exécution.

C'est aussi ce qui règle la lacune notée dans la spec (« les polices retenues ne sont pas
toutes fournies par le design system ») : Montserrat, absente de `project/fonts/`, est
approvisionnée par le même chemin que Lato — rien à committer, rien à gérer à la main.

**À vérifier à l'implémentation** : que `Lato` et `Montserrat` répondent bien chez Bunny aux
graisses demandées ; un `npm run build` qui échoue le dit immédiatement. Repli en cas
d'absence : `local()` avec les `.woff2` de Lato copiés du design system, et Montserrat
récupérée à la main — plus de fichiers dans le dépôt, même résultat pour l'utilisateur.

**Alternatives écartées** : la balise `<link>` vers Google Fonts que porte la maquette —
c'est précisément ce que FR-008 refuse, et une requête tierce sur l'écran de connexion
raconte à un tiers qui se connecte et quand ; `@fontsource` en dépendance npm, qui fait le
même travail au prix d'un paquet de plus, alors que le plugin est déjà installé.

**Conséquence sur le repli** (cas limite de la spec, polices distantes bloquées) : les
`@font-face` étant servis par le produit, « bloquer les polices distantes » ne s'applique
plus. Reste le cas d'un navigateur qui refuse toute police web : les piles de repli du DS —
`system-ui` derrière Lato, `system-ui` derrière Montserrat — donnent un écran encore lisible.
Les métriques de repli optimisées du plugin (`optimizedFallbacks`, actif par défaut) limitent
le décalage de mise en page.

---

## D-005 — Le logo est un SVG inséré dans le balisage, pas un fichier public

**Décision** : un composant `<x-oidc::brand.logo>` porte le SVG en ligne, en deux variantes
— claire pour l'aplat noir, sombre pour la barre de la page connectée. Les sources viennent
du design system par identifiant d'asset, jamais redessinées.

| Variante | Asset du DS | Usage |
|----------|-------------|-------|
| claire | `logo-dailyapps-light.svg` (`a3374513b2295aaa194dcb3696c299fb`) | aplat de marque, fond noir |
| sombre | `logo-dailyapps-dark.svg` (`75cd90371fbd81b37c9ac3acb91d4a2c`) | barre haute de `/account`, fond blanc |

Le fichier récupéré a été inspecté : `viewBox="0 0 225 32"`, mot-symbole en blanc et chevron
en `#E00C1A` pour la variante claire. **Il embarque un manifeste C2PA de 7,7 Ko** dans une
balise `<metadata>` — presque la moitié du fichier. Elle est retirée à la reprise ; le SVG
utile fait 8,2 Ko.

**Rationale** : en ligne, la marque s'affiche dans le même aller-retour que la page — aucune
requête supplémentaire, et surtout aucun instant où l'écran de connexion est là sans sa
marque. FR-002 tient l'identification visuelle pour une défense contre l'hameçonnage : une
marque qui arrive une demi-seconde après le formulaire ne défend rien. En ligne, le SVG vit
aussi dans la couche, là où la constitution veut qu'il soit.

**Alternatives écartées** : `api/public/brand/*.svg` — deux requêtes de plus, un dossier
d'assets hors couche, et rien qui interdise au fichier de manquer en production ; une image
matricielle, qui perd la netteté sur écran dense.

Même chemin pour le favicon, aujourd'hui celui de Laravel : `logo-tile-red-light.svg`
(`3acd2044407a38f14c628fa77f3d69b4`) remplace `api/public/favicon.ico`. C'est la marque que
l'utilisateur voit dans son onglet et dans ses favoris — le seul endroit du parcours où un
fichier public reste le bon support, faute d'alternative.

---

## D-006 — L'invitation périmée garde son 410 et gagne un écran

**Décision** : `AcceptInvitation::mount` lève une exception dédiée
`InvitationNoLongerValid`, dont la méthode `render()` renvoie la vue de la couche avec le
statut **410**. `abort_if(..., 410)` disparaît, le code de statut ne bouge pas.

**Rationale** : trois tests de `AcceptInvitationScreenTest` affirment `assertStatus(410)` —
invitation périmée, invitation déjà consommée, jeton que personne n'a émis. SC-002 interdit
de les toucher. Un 410 est par ailleurs la bonne réponse : la ressource est partie, et
redemander la même URL n'y changera rien. Ce qui manque n'est pas un autre statut, c'est un
corps de réponse : aujourd'hui l'utilisateur reçoit la page d'erreur nue de Laravel.

Laravel appelle `render()` sur une exception qui en porte une. La vue vit dans la couche, le
statut reste 410, et la page porte l'identité comme les six autres.

**Alternatives écartées** : ajouter `api/resources/views/errors/410.blade.php` — hors couche,
et surtout une page 410 générique rédigée pour les invitations mentirait le jour où un autre
chemin répondra 410 ; brancher la vue par le `Handler` de `technical/framework`, ce qui ferait
connaître l'invitation à une couche qui n'a pas à la connaître.

**Cas limite tranché** : périmée, déjà consommée, jamais émise — `Invitation::pending()` ne
les distingue pas, et les distinguer serait un oracle (« ce jeton a existé »). Les trois cas
mènent au même écran et au même message, `oidc::screens.invitation.expired`, déjà traduit.

---

## D-007 — Le lien de réinitialisation périmé se dit à l'ouverture, quand c'est possible

**Décision** : `ResetPassword::mount` vérifie le jeton lorsque l'adresse accompagne le lien,
et bascule l'écran sur son état « lien expiré » — explication et bouton « Demander un nouveau
lien » vers `password.forgot`. Statut 200. Sans adresse dans l'URL, l'écran se comporte
comme aujourd'hui : le formulaire s'affiche et l'invalidité se dit à la soumission.

**Rationale** : FR-009 veut l'explication *quand l'utilisateur ouvre le lien*. Le courriel de
réinitialisation — `PasswordResetRequested::resetUrl()` — construit toujours l'URL avec
`?email=`, donc le cas nominal a de quoi vérifier. Le repli existe pour un lien tronqué ou
recopié à la main, où vérifier est impossible : mieux vaut le formulaire d'aujourd'hui qu'un
écran d'expiration affirmé à tort.

Le contrôle porte sur `Password::broker()->getRepository()->exists($user, $token)`, qui lit
le jeton sans le consommer. Il n'ouvre pas d'oracle d'existence de compte : une adresse
inconnue et un jeton faux donnent le même écran.

**Ce qui ne bouge pas** : le contrôle à la soumission reste en place et reste le gardien —
un jeton qui expire entre l'affichage et l'envoi est toujours refusé par `Password::reset`.
Aucun test n'interroge `GET /password/reset/{token}` ; les dix tests de `PasswordResetTest`
passent par `Livewire::test`, où `mount` reçoit le jeton sans adresse et prend donc le repli.
FR-004 est tenu au sens où il compte : validations, redirections et messages sont les mêmes.

**Alternatives écartées** : répondre 410 comme pour l'invitation — l'écran doit porter une
action (« demander un nouveau lien »), et une page d'erreur qui propose un bouton est un
contresens ; ne rien vérifier et laisser l'utilisateur saisir deux fois un mot de passe pour
apprendre ensuite que le lien était mort — c'est l'impasse que la user story 2 vient fermer.

**Cas limite tranché** : un lien déjà consommé et un lien simplement périmé aboutissent au
même écran. Laravel supprime le jeton à l'usage ; les deux cas sont indistinguables au niveau
du dépôt de jetons, et les distinguer apprendrait à un tiers qu'un lien a servi.

---

## D-008 — Les composants sont écrits en Blade, pas repris du design system

**Décision** : les contrôles du parcours sont des composants Blade anonymes de la couche
`oidc`, appelés `<x-oidc::field>`, `<x-oidc::button>` et ainsi de suite.

**Rationale** : le XEFI Design System livre ses composants en **React**
(`project/components/bundle.js`, lu depuis `window.XEFIDesignSystem_1dd81f`). La stack est
arrêtée par la constitution : Laravel + Livewire, un seul déployable, aucun second front sans
amendement. Monter React pour cinq formulaires introduirait précisément le front que la
feature 001 a retiré. Ce qui se reprend du DS, ce sont ses **valeurs** (D-001) et ses
**formes** — hauteurs de contrôle, rayons, tons de feedback — pas son code.

`loadViewsFrom($path, 'oidc')` suffit : Laravel résout `<x-oidc::field>` en
`oidc::components.field`, sans rien enregistrer de plus. Le provider le fait déjà pour les
vues des cinq écrans.

**Alternatives écartées** : charger le bundle React et monter les contrôles dans des îlots —
un second runtime front, un pont Livewire à écrire, et des champs que Livewire ne voit plus ;
un paquet Blade tiers (Flux, Mary, Filament Forms), qui apporte sa propre identité à
contredire token par token, pour douze composants qu'on écrit une fois.

**Écart consigné** : la constitution veut qu'un paquet passe avant du code écrit à la main.
Aucun des paquets qu'elle nomme ne fournit de contrôles Blade, et la seule source arbitrée —
le DS — n'est pas consommable ici. L'écart est porté au tableau de complexité du plan.

---

## D-009 — Deux coquilles, pas une

**Décision** : `layouts.screen` (existante, refondue) sert les écrans d'entrée — aplat de
marque à gauche, contenu à droite, largeur utile 400 px. `layouts.app` (neuve) sert les pages
connectées — barre haute portant la marque, l'adresse et la déconnexion, contenu centré à
720 px en cartes. `Account` bascule sur la seconde.

**Rationale** : la maquette les traite comme deux objets — l'aplat vend le produit à qui n'est
pas encore entré, la barre haute situe qui l'est déjà. Les deux partagent les mêmes contrôles,
ce que SC-001 demande ; ce sont les coquilles qui diffèrent, pas les composants.

**Réponse au cas limite de la spec** (aplat sur écran étroit) : l'aplat est masqué sous
1024 px et la colonne de formulaire prend toute la largeur, avec la marque reportée au-dessus
du titre. L'écran étroit garde ainsi la marque — FR-002 vaut sur téléphone comme sur poste —
sans payer un aplat qui dévorerait le premier écran de défilement.

---

## D-010 — Une erreur de validation et un échec d'authentification cohabitent

**Décision** : les erreurs propres à un champ restent sous leur champ ; l'échec global —
identifiants refusés, compte désactivé, organisation suspendue, trop de tentatives — monte
dans un bandeau `<x-oidc::alert tone="error">` en haut du formulaire.

**Rationale** : c'est le cas limite que la spec pose. Aujourd'hui `Login::fail()` accroche le
message global à `email` via `addError('email', ...)`, si bien qu'un échec d'authentification
s'affiche sous le champ d'adresse, à l'endroit où un « adresse invalide » s'afficherait —
deux choses de nature différente au même endroit.

**Contrainte ferme** : `fail()` ne change pas de mécanique. `LoginScreenTest` vérifie les
erreurs sur la clé `email`, et FR-004 gèle le comportement. La vue lit donc `$errors` et
décide de l'endroit : si le message porté par `email` est l'un des messages
d'`oidc::auth.*`, il va au bandeau ; sinon il reste sous le champ. Les deux peuvent
apparaître ensemble sans se chevaucher.

Le message lui-même ne bouge pas d'un caractère — `oidc::auth.failed` ne dit toujours pas si
le compte existe, ce que la constitution impose et que le scénario d'acceptation 2 vérifie.

---

## D-011 — La preuve se fait en PHPUnit, sur la même suite

**Décision** : les tests neufs rejoignent `api/technical/oidc/tests/Feature/`, lancés par
`./vendor/bin/sail test`. Aucun outil de capture visuelle n'est introduit.

Ce qu'un test peut établir ici : que les deux écrans neufs répondent avec le bon statut et le
bon message ; que chaque écran monte la coquille attendue et porte la marque ; que les clés de
traduction employées existent en français et en anglais (SC-004 se teste, en comparant les
arborescences des deux fichiers `screens.php`) ; qu'aucun écran ne définit un contrôle qui lui
soit propre (SC-001 se teste, en cherchant les attributs `class` bruts dans les vues d'écran).

Ce qu'un test ne peut pas établir et qui reste à la vérification manuelle du `quickstart.md` :
la ressemblance à la maquette, et SC-005 — qu'un utilisateur distingue l'écran authentique
d'une imitation sans marque.

**Alternative écartée** : ajouter Dusk ou une comparaison de captures pour tenir SC-001
visuellement — une suite de plus, une dépendance de navigateur dans la CI, et des tests qui
rougissent au premier pixel déplacé, alors que la constitution tient à une seule suite.
