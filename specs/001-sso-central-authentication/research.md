# Phase 0 — Recherche : Authentification centralisée (SSO) DailyApps

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-09-17

Chaque décision ci-dessous lève une inconnue du Technical Context du plan. Les versions citées
ont été relevées sur Packagist et sur la documentation Laravel 13 le 2026-09-17, pas de mémoire.

**Révision du 2026-09-17** — D4 a été reprise. Sa première rédaction affirmait que l'api n'avait plus
de couche de vues, `osdd:start` les ayant supprimées : c'était faux. `api/resources/views/`, Vite 8,
Tailwind 4 et un `routes/web.php` qui retourne une vue Blade sont tous en place ; `osdd:start` a
supprimé `app/`, `config/` et `database/` à la racine, pas les vues. La décision est donc inversée :
l'écran de connexion vit dans l'api, en Livewire, et le dépôt `front` a été retiré du workspace.
D13 et D14 suivent.

---

## D1 — Protocole entre les applications et le point central

**Décision** : OpenID Connect par-dessus OAuth 2.0, flux *Authorization Code* avec PKCE obligatoire
pour tous les clients. L'`id_token` porte l'identité et les rôles ; l'`access_token` sert à
interroger le point central.

**Rationale** : FR-002 (identifier puis rendre l'utilisateur avec ses droits), FR-003 (retour sur la
page visée), FR-006 (adresses de retour déclarées) et FR-016 (rôles par application) sont la
définition littérale d'un flux OIDC. Le construire à la main reviendrait à réécrire un standard
audité. PKCE pour tous, y compris les clients confidentiels : parmi les quinze applications à venir,
celles qui s'exécutent dans un navigateur ou sur un téléphone sont des clients publics, et uniformiser
évite deux chemins de code à sécuriser.

**Alternatives écartées** :
- *Jeton maison partagé par cookie de domaine* : ne tient que si les quinze applications sont sur le
  même domaine parent, ce que rien ne garantit, et n'offre rien pour le mobile.
- *SAML 2.0* : pertinent pour raccorder des logiciels du marché, hors périmètre (hypothèse de la
  spec). Plus lourd, XML, mal adapté au mobile.

---

## D2 — Construire le fournisseur d'identité, ou en déployer un

**Décision** : le construire dans le dépôt `api`, avec **`laravel/passport` ^13.8** pour le serveur
OAuth 2.0 et **`jeremy379/laravel-openid-connect` ^3.3** pour la couche OIDC.

**Rationale** : le cœur de valeur du produit n'est pas l'émission de jetons — c'est la relation
organisation × licence × siège × accès, qui décide *qui a le droit d'entrer où*. Un IdP externe
obligerait à tenir cette relation dans l'api et à la republier dans l'IdP pour qu'il la mette dans les
jetons : deux sources, une synchronisation, et la question « pourquoi cet accès a-t-il été refusé »
sans réponse simple.

Relevés du 2026-09-17 :

| Paquet | Dernière version | Compatibilité | Adoption | Verdict |
|--------|------------------|---------------|----------|---------|
| `laravel/passport` | v13.8.0 (2026-08-28) | `illuminate/* ^13.0`, PHP ^8.2 | 3,4 M/mois | Retenu — officiel Laravel |
| `jeremy379/laravel-openid-connect` | 3.3.0 (2026-06-30) | `laravel/passport ^13.0`, `laravel/framework ^12\|^13` | 51 k/mois, 64 ★ | Retenu — seul à déclarer Laravel 13 |
| `admin9/laravel-oidc-server` | v1.2.0 (2026-06-29) | `laravel/passport ^12\|^13` | 2,4 k/mois, 3 ★ | Écarté — trop jeune pour une brique critique |
| `ronvanderheijden/openid-connect` | 1.2.1 (2024-07-23) | PHP `^7.4\|^8.0` | — | Écarté — sans release depuis deux ans, PHP 8.4 non déclaré |

Passport 13 couvre nativement *authorization code*, PKCE, *client credentials*, *refresh* et *device*,
la configuration des durées de vie (`Passport::tokensExpireIn`), la révocation (`$token->revoke()`) et
la purge planifiée (`passport:purge`). Le paquet OIDC ajoute `/.well-known/openid-configuration`, le
JWKS, l'`id_token` et `/oauth/userinfo`, avec les claims composés par une `IdentityEntity`.

**Alternatives écartées** :
- *Keycloak / Zitadel / Authentik* : produits solides, mais ils déplacent le problème sans le
  résoudre — le modèle de licences reste à construire à côté, et s'y ajoute l'exploitation d'un
  service supplémentaire. Disproportionné pour quinze applications internes.
- *`league/oauth2-server` nu* : c'est ce que Passport encapsule. S'en passer, c'est reprendre à sa
  charge les migrations, les commandes de clés et les contrôleurs, sans rien gagner.

---

## D3 — Ce que le paquet OIDC ne fait pas : la déconnexion globale

**Décision** : implémenter le **back-channel logout** nous-mêmes, dans `technical/oidc`. À la
fermeture d'une session (FR-034), à la désactivation d'un compte (FR-036), à la suspension d'une
organisation (FR-021), à la résiliation d'une licence (FR-023) et au changement de mot de passe
(FR-012), le point central révoque les jetons concernés **et** pousse une notification signée vers
l'URL de déconnexion déclarée par chaque application ayant une session vivante, avec file d'attente et
réessais.

**Rationale** : c'est le trou le plus important du plan, et il faut le nommer. `jeremy379/laravel-openid-connect`
n'implémente ni `end_session_endpoint` ni l'introspection. Surtout, un `access_token` OIDC est un JWT
auto-porteur : une application qui le valide localement via le JWKS ne voit **jamais** qu'il a été
révoqué en base. Sans poussée, la seule façon de tenir SC-005 (coupure sous une minute) serait une
durée de vie de jeton d'une minute — inexploitable.

Le dispositif retenu tient SC-005 par la poussée, et la durée de vie courte sert de filet quand une
application est injoignable :

- `access_token` : 15 minutes ; `refresh_token` : 8 heures glissantes, rotation à chaque usage.
- Chaque rafraîchissement revérifie l'état du compte, de l'organisation et de la licence.
- La poussée de déconnexion est un job en file avec réessais exponentiels ; un échec définitif est
  journalisé comme événement de sécurité.

**Alternatives écartées** :
- *Introspection à chaque requête* : chaque application appellerait le point central à chaque appel.
  Transforme le SSO en point de contention et aggrave le risque de SC-006.
- *Front-channel logout par iframes* : ne fonctionne pas si l'onglet est fermé, et les navigateurs
  bloquent de plus en plus les cookies tiers.

---

## D4 — Où vit l'écran de connexion

**Décision** : dans l'api, en **Livewire ^4.4**, servi par le même déployable que
`/oauth/authorize`. Le dépôt `front` (Nuxt) est retiré du workspace.

**Rationale** : trois choses convergent.

D'abord le périmètre. L'arbitrage Q1 de la spec a sorti le portail et l'administration de ce produit.
Ce qui reste d'IHM tient en cinq pages de formulaires — connexion, mot de passe oublié,
réinitialisation, acceptation d'invitation, profil. Le `CLAUDE.md` du workspace justifiait Nuxt par
« a workspace exists because the product spans repositories, which is exactly the case a Livewire
monolith is not » : cette prémisse est partie avec le portail.

Ensuite la stack maison. `global:default-project-stack` fait de Laravel + Livewire la stack Xefi par
défaut. Nuxt était la dérogation ; elle n'a plus de motif.

Surtout, cela **supprime une contrainte de déploiement** au lieu de l'aménager. Avec un front séparé,
l'écran de connexion et `/oauth/authorize` sont sur deux origines : il faut un domaine parent commun,
un `SESSION_DOMAIN` partagé, la protection CSRF inter-origines, et une validation de l'URL de retour
pour que l'écran de connexion ne serve pas de tremplin vers un site tiers. En monolithe, la page de
connexion **est** l'application qui héberge `/oauth/authorize` : Passport redirige un visiteur non
identifié vers `route('login')`, même session, même origine. C'est son montage canonique, et tout ce
paragraphe de contrainte disparaît.

Accessoirement, le point central est un point de défaillance unique pour quinze applications
(SC-006) : un seul déployable, c'est moitié moins de surface de panne qu'un front et une api dont
l'un en carafe empêche toute connexion.

**Ce qu'il faut savoir avant de commencer** : la documentation de `xefi/laravel-osdd` décrit une
couche comme possédant « models, migrations, seeders » et ne mentionne nulle part les vues, Blade,
Livewire ni les routes. Cela fonctionnera — une couche est un paquet Composer avec son service
provider, donc `loadViewsFrom()` et l'enregistrement de composants Livewire s'y comportent comme dans
n'importe quel paquet — mais on utilise le système de couches là où sa documentation ne va pas. À
vérifier sur la première couche qui porte une vue, pas à découvrir sur la cinquième.

Livewire v4.4.5 (2026-09-14) déclare `illuminate/support ^13.0` : compatible.

**Alternatives écartées** :
- *Front Nuxt séparé* : le montage initialement prévu. Il facturait un second déployable, un second
  arbre de dépendances et la contrainte de domaine partagé, pour cinq formulaires.
- *Front Nuxt devenant client OAuth de lui-même* : évite le domaine partagé, mais ajoute un
  aller-retour et rend le débogage circulaire.

**Conséquence sur la charte** : si le portail — produit distinct — finit en Vue, l'utilisateur verra
la page de connexion puis le portail coup sur coup, avec deux systèmes de design. Tailwind 4 est déjà
installé dans l'api ; les tokens se partagent. À traiter quand le portail sera spécifié, pas avant.

---

## D5 — Consentement

**Décision** : pas d'écran de consentement. Le modèle `Client` de Passport est étendu et
`skipsAuthorization()` renvoie vrai pour les clients *first-party*, ce que sont les quinze
applications.

**Rationale** : le consentement OAuth existe pour qu'un utilisateur autorise un tiers à accéder à ses
données. Ici l'éditeur des quinze applications est le même que celui du point central : demander
« autorisez-vous DailyApps Congés à accéder à DailyApps ? » n'apporte rien et casse la promesse de
SC-002. Le jour où une application tierce se raccordera, elle sera déclarée non *first-party* et le
consentement reviendra pour elle seule — le mécanisme est déjà là.

---

## D6 — Rôles applicatifs et permissions : deux choses distinctes

**Décision** : deux mécanismes séparés, jamais confondus.

- **`spatie/laravel-permission`** (déjà installé, couche `technical/permissions`) gouverne ce qu'un
  utilisateur a le droit de faire **dans l'api du point central** : déclarer une organisation,
  attribuer une licence, inviter. Vérifié par permission, jamais par nom de rôle.
- **Les rôles applicatifs** (FR-030, FR-016) sont une entité métier du catalogue : chaque application
  déclare les rôles qu'elle expose, on les attribue sur un accès, ils voyagent dans l'`id_token`. Ils
  ne sont ni des rôles ni des permissions spatie.

**Rationale** : les deux mots se ressemblent et la confusion coûterait cher. Stocker les rôles
applicatifs dans spatie mettrait dans une même table les droits d'administration du point central et
ceux de quinze applications étrangères, avec des collisions de noms garanties dès la deuxième
application qui déclare un rôle `manager`.

Le périmètre de lecture et d'écriture d'un administrateur client (FR-028) passe par
`lomkit/laravel-access-control` : un `Control` par modèle, avec le périmètre « ma seule organisation ».

---

## D7 — Découpage en couches OSDD

**Décision** : quatre couches fonctionnelles et deux couches techniques nouvelles, en plus des trois
existantes.

| Couche | Nature | Ce qu'elle détient |
|--------|--------|--------------------|
| `functional/users` *(existante, étendue)* | fonctionnelle | identité, mot de passe, invitation, réinitialisation, cycle de vie du compte |
| `functional/organizations` | fonctionnelle | organisations clientes, rattachement, rôle dans l'organisation, suspension |
| `functional/catalog` | fonctionnelle | applications de l'écosystème, adresses de retour, rôles exposés, état au catalogue |
| `functional/licensing` | fonctionnelle | licences, sièges, accès applicatifs, rôles attribués |
| `technical/oidc` | technique | Passport + couche OIDC, composition des claims, back-channel logout |
| `technical/audit` | technique | journal des événements de sécurité et sa rétention |
| `technical/framework`, `technical/permissions`, `technical/osdd` *(existantes)* | technique | inchangées |

**Pourquoi licences et accès dans la même couche** : un accès consomme un siège d'une licence. Séparer
les deux mettrait le décompte dans une couche et sa consommation dans une autre, et la règle de
FR-024 traverserait une frontière de couche à chaque attribution.

**Pourquoi `oidc` est technique et non fonctionnel** : la couche ne détient aucune donnée métier. Elle
expose un point d'extension — un contrat de fournisseur de claims — que `functional/licensing`
implémente pour y verser les applications et les rôles. La dépendance va donc du fonctionnel vers le
technique, jamais l'inverse.

---

## D8 — Surface HTTP

**Décision** :

- **CRUD → `lomkit/laravel-rest-api`** (déjà installé) : organisations, applications, licences, accès,
  utilisateurs, événements de sécurité. Une `Resource` par modèle, le périmètre venant du `Control`
  `lomkit/laravel-access-control` correspondant.
- **Non-CRUD → contrôleurs classiques** : les routes OIDC (fournies par Passport et le paquet OIDC),
  la connexion et la déconnexion de session, le mot de passe oublié, l'acceptation d'invitation, la
  liste « mes applications », et la rotation d'un secret client.

**Rationale** : règle maison `laravel:preferred-packages` — le CRUD passe par le paquet, le reste
reste en contrôleurs. « Mes applications » (FR-014) n'est pas un CRUD : c'est une question dont la
réponse croise licence, accès et état du compte, et le portail est son seul appelant.

URIs au pluriel et imbrication d'un niveau maximum (`laravel:api-routing`) :
`/organizations/{id}/licences` pour la collection, `/licences/{id}` pour le membre.

---

## D9 — Cycles de vie

**Décision** : le compte utilisateur (`invited → active → disabled → active`) reçoit le patron State,
une classe par état, transitions illégales levant une exception. L'organisation (`active ⇄ suspended`)
et l'application au catalogue (`draft → published → retired`) restent un enum PHP adossé à une garde
de transition.

**Rationale** : `design-patterns:state` ne s'applique que si le même objet traverse les états, si
plus d'une méthode se comporte différemment selon l'état, et si certaines transitions sont illégales.
Le compte coche les trois : il peut ou non s'authentifier, apparaît ou non dans les accès, consomme ou
non un siège, et « invité » ne se retrouve pas depuis « désactivé ». L'organisation est une bascule
booléenne déguisée, l'application n'a qu'un comportement variable — un patron complet y serait de la
cérémonie.

Les états sont des enums PHP, jamais des colonnes `ENUM` MySQL (`laravel:no-db-enums`).

---

## D10 — Journal de sécurité

**Décision** : un modèle dédié `SecurityEvent` dans `technical/audit`, avec `Prunable` réglé sur
douze mois, plutôt que `spatie/laravel-activitylog`.

**Rationale** : FR-037 demande de tracer des échecs d'identification et des poussées de déconnexion
qui ne sont la modification d'aucun modèle — hors du champ d'activitylog, qui suit les changements
Eloquent. FR-039 impose douze mois : `laravel:retention-via-prunable` en fait une propriété du modèle
plutôt qu'une commande de ménage à écrire. La purge se fait par lots, jamais en masse
(`laravel:no-mass-prunable`).

---

## D11 — Concurrence sur les sièges

**Décision** : l'attribution d'un accès s'exécute dans une transaction qui verrouille la ligne de
licence (`lockForUpdate`) avant de compter les sièges occupés.

**Rationale** : FR-024 est une règle de comptage. Deux administrateurs qui attribuent en même temps le
dernier siège passeraient tous les deux un contrôle naïf. Le verrou sur la licence est le plus petit
périmètre qui rende la règle vraie.

---

## D12 — Secrets des applications raccordées

**Décision** : le secret client est haché en base et affiché une seule fois, à la création et à
chaque rotation. La rotation et la révocation sont des opérations par application (FR-033), sans
effet sur les autres.

**Rationale** : c'est le comportement de Passport depuis la v11 (secrets hachés) et la seule posture
tenable — un secret relisible en base est un secret partagé avec quiconque lit la base.

---

## D13 — Tests

**Décision** :

PHPUnit 12.5, déjà en place, exécuté via `./vendor/bin/sail test`. Un seul lanceur pour tout, y
compris l'IHM : les composants Livewire se testent avec `Livewire::test(...)` dans la même suite que
le reste, sans second outillage.

- **Feature** : les flux HTTP de bout en bout — connexion, `/oauth/authorize` avec et sans session,
  `redirect_uri` non déclarée, refus pour licence absente, poussée de déconnexion.
- **Unit** : les transitions d'état du compte et le décompte de sièges sous verrou.
- **Livewire** : les cinq écrans, en particulier le message identique de FR-007 et la limitation de
  débit de FR-008.

Factories via le helper `faker()` de `xefi/faker-php-laravel`, jamais `fakerphp/faker`.
`osdd:phpunit` synchronise `phpunit.xml` avec la suite de chaque couche — à relancer après la
création de chacune.

**Rationale** : `global:test-new-features` exige des tests sur toute fonctionnalité nouvelle. La
bascule en monolithe fait disparaître le trou signalé dans la version précédente de ce document — il
n'y a plus de dépôt front sans lanceur de tests à équiper.

---

## D14 — Le dépôt mobile

**Décision** : `mobile` n'est pas touché par cette feature. Aucune branche, aucun commit.

**Rationale** : hypothèse de la spec — un point d'authentification n'a pas d'application native
propre. Le squelette Flutter attend la première application métier. À noter pour
`speckit.multirepo.branch`, qui branche par défaut tous les dépôts déclarés : depuis le retrait du
`front`, `repos.yml` en déclare deux, et la feature n'en concerne qu'un — `api`. Aucun commit ne doit
atterrir dans `mobile`.
