# DailyApps SSO Constitution

Ce document gouverne le produit **DailyApps SSO** — le fournisseur d'identité unique de
l'écosystème DailyApps — et l'ensemble des dépôts déclarés dans `repos.yml`. Il prime sur toute
autre pratique, habitude ou préférence locale.

## Core Principles

### I. Une seule source de vérité pour l'identité et les droits

Le point central détient l'identité, les organisations, les licences, les accès et les rôles.
Aucune application raccordée NE DOIT tenir son propre annuaire, ni recopier une liste de droits,
ni dériver un droit d'un identifiant qu'elle stocke. Un droit est le croisement de quatre choses —
licence valide de l'organisation, accès attribué, état du compte, état de l'organisation — et ce
croisement DOIT être calculé par le point central, jamais reconstitué par son consommateur. Les
applications reçoivent des *claims* et des réponses, jamais une table à synchroniser.

*Rationale* : quinze applications qui recopient chacune les droits dans leur coin, c'est quinze
vérités divergentes et un écosystème ingouvernable. C'est la raison d'être du produit, et SC-010
le mesure : une application raccordée ne conserve aucune liste d'utilisateurs ni de droits qui lui
soit propre.

### II. Le raccordement passe par le standard, jamais par du sur-mesure

Toute application se raccorde en **OpenID Connect sur OAuth 2.0**, flux *authorization code* avec
**PKCE obligatoire**. Raccorder la seizième application DOIT se réduire à déclarer un client :
aucune modification du code du point central, aucun endpoint dédié à une application, aucun
partage de session par cookie inter-domaines, aucun canal privé négocié au cas par cas. Une
surface exposée à une application est exposée à toutes, ou elle n'existe pas.

*Rationale* : SC-004 en fait un critère de succès. Un raccordement sur-mesure est une dette qui se
multiplie par quinze, et chaque écart au standard est une faille d'authentification que personne
n'a revue.

### III. Refus par défaut, et jamais sur un nom de rôle

L'accès est refusé tant qu'il n'est pas explicitement accordé. Toute vérification d'autorisation
DOIT porter sur une **permission**, jamais sur un nom de rôle : les rôles applicatifs — ce qu'un
utilisateur est dans une application cliente — et les permissions — ce qu'il a le droit de faire
ici — sont deux mécanismes distincts qui NE DOIVENT PAS être confondus. Une application qui
interroge le point central n'obtient que ce qui la concerne : les droits d'un tiers ou les accès
sur une autre application DOIVENT être refusés.

*Rationale* : un nom de rôle est une chaîne de caractères qui change de sens le jour où le métier
change, et un test sur cette chaîne devient silencieusement faux. Une permission se révoque ; un
rôle se renomme.

### IV. La révocation est immédiate et traçable

Tout chemin d'accès neuf DOIT répondre à la question « comment on le coupe » avant d'être
fusionné. Désactiver un compte ou retirer un accès DOIT couper l'accès à toutes les applications
en moins d'une minute (SC-005) — ce que des jetons courts, la rotation des jetons de
rafraîchissement et le *back-channel logout* rendent possible, et qu'un jeton longue durée validé
hors ligne rend impossible. Tout événement de sécurité — connexion, échec, invitation,
attribution et retrait d'accès, révocation — DOIT être journalisé dans le journal dédié, avec une
rétention explicite.

*Rationale* : un SSO sans révocation effective est un trousseau de clés qu'on ne peut pas
reprendre. C'est le risque propre au fait de centraliser, et c'est la contrepartie qui justifie la
centralisation.

### V. Le code vit en couches OSDD

Le dépôt `api` est organisé en couches `xefi/laravel-osdd` — `functional/` pour les domaines
métier, `technical/` pour l'infrastructure transverse. Aucune fonctionnalité NE DOIT vivre hors
d'une couche : il n'y a ni `app/`, ni `database/`, ni `config/` à la racine, et ils NE DOIVENT PAS
être recréés. Les commandes `osdd:*` remplacent les `make:*`. Une couche est autonome : elle porte
ses modèles, ses migrations, ses tests et son service provider, et ses réactions au cycle de vie
passent par des événements et des listeners déclarés dans ce provider — jamais par un observer.

*Rationale* : c'est l'architecture de référence Xefi, et c'est ce qui permettra d'extraire une
couche vers une autre application de l'écosystème plutôt que de la réécrire.

### VI. Rien n'est livré sans test

Toute fonctionnalité neuve DOIT être couverte par un test avant d'être considérée comme faite. Une
seule suite, PHPUnit, lancée par `./vendor/bin/sail test` : les écrans Livewire s'y testent comme
le reste, avec `Livewire::test(...)`. Les données de test viennent de factories, jamais de
fixtures écrites à la main. Un test qui ne passe pas rend la tâche non terminée — le rapport de
`/speckit-implement` se prend au pied de la lettre, il ne se contourne pas.

*Rationale* : sur la brique dont dépendent quinze applications, une régression non détectée coupe
l'accès à tout le monde en même temps.

## Contraintes techniques et de sécurité

**Stack.** Laravel + Livewire est la stack par défaut, servie par un déployable unique : l'écran
de connexion et `/oauth/authorize` partagent l'origine et la session. Aucun second front n'est
introduit sans amendement de ce document.

**Paquets avant code.** Le CRUD passe par `lomkit/laravel-rest-api`, les périmètres d'accès par
`lomkit/laravel-access-control`, les permissions par `spatie/laravel-permission`, les couches par
`xefi/laravel-osdd`, les factories par le helper `faker()` de `xefi/faker-php-laravel`. Écrire à
la main ce que l'un de ces paquets fournit DOIT être justifié dans le plan de la feature, dans le
tableau des écarts.

**Base de données.** Aucun `onDelete('cascade')`, aucune cascade au niveau du schéma : une
suppression en cascade passe par un listener sur l'événement `deleting` du parent, pour que les
listeners des enfants se déclenchent. Les statuts sont des colonnes portées par des énumérations
applicatives, jamais des types `enum` en base.

**Secrets.** Le secret d'une application raccordée est haché en base et affiché une seule fois, à
sa création et à sa rotation. Aucun secret, aucun jeton, aucun mot de passe ne figure en clair
dans un journal, une réponse d'API ou un message d'erreur. Un message d'échec d'authentification
NE DOIT PAS révéler si un compte existe.

**Interface.** Aucun HTML concaténé dans une classe PHP — le balisage vit en Blade. Aucun texte
destiné à un utilisateur en dur dans le code : tout passe par les fichiers de traduction.

**Documentation.** Rien n'est créé hors de `specs/`. Les `CLAUDE.md` existants sont mis à jour, pas
augmentés d'un dossier `docs/` ni d'un fichier d'architecture. Le code est la documentation.

**Commandes.** Dans `api`, tout `artisan`, `composer` et test passe par `./vendor/bin/sail`, jamais
sur l'hôte.

## Workflow de développement et portes de qualité

**La session s'ouvre à la racine du workspace.** Spec-kit résout son projet en remontant vers
`.specify/` ; ouvrir une session dans un dépôt enfant met les specs hors de portée. Aucun
`specify init` dans un enfant.

**Tout chemin écrit commence par le dépôt** — `api/functional/users/...`, jamais `functional/...`.
Il n'y a pas de dépôt par défaut dans un workspace, même quand un seul est actif.

**Le `CLAUDE.md` d'un dépôt se lit avant d'y toucher.** Un enfant sans `CLAUDE.md` est une lacune à
signaler, pas une permission de deviner ses conventions.

**`staging` est le tronc.** Les branches de feature sont coupées de `staging` par
`speckit.multirepo.branch`. `main` est la branche de livraison et n'avance que par *fast-forward*
de `staging`. Jamais de branche de feature depuis `main`, jamais de fusion directe dans `main`.

**Une merge request par dépôt**, croisées par le numéro de feature. Elles fusionnent dans l'ordre
des dépendances : le fournisseur d'abord. Une MR consommatrice reste ouverte tant que son
fournisseur n'est pas fusionné et déployé.

**La porte constitutionnelle est instruite, pas cochée.** Le `Constitution Check` d'un `plan.md`
DOIT nommer chaque principe confronté et dire comment le plan s'y tient. Un écart se justifie dans
le tableau de complexité, avec l'alternative plus simple écartée et la raison de l'écarter. Un
écart non écrit est une violation.

**Une feature n'est finie que lorsque `speckit.multirepo.status` est propre** pour chaque dépôt
concerné : rien de non commité, la bonne branche, rien de non poussé. Un dépôt sur la mauvaise
branche se traite comme du travail qui a peut-être atterri sur un tronc, et se vérifie avant toute
autre chose.

## Governance

Cette constitution prime sur toute autre pratique. En cas de contradiction entre ce document, un
`CLAUDE.md` et une habitude de dépôt, c'est ce document qui tranche.

**Amendement.** Un amendement se propose par `/speckit-constitution`, qui réécrit ce fichier et
produit un rapport d'impact. Il est commité séparément du code qu'il gouverne, avec un message qui
énonce la raison du changement. Un amendement qui invalide du code existant DOIT dire ce qui reste
en l'état et ce qui doit être repris — un principe neuf ne réécrit pas rétroactivement l'histoire
du dépôt.

**Versionnage.** Versionnage sémantique du document lui-même :

- **MAJOR** — un principe est retiré ou redéfini d'une manière qui rend non conforme du code
  jusque-là conforme.
- **MINOR** — un principe ou une section est ajouté, ou sa portée est matériellement élargie.
- **PATCH** — clarification, reformulation, correction, sans changement de portée.

**Conformité.** Chaque `plan.md` instruit la porte `Constitution Check` avant la phase 0 et la
ré-instruit après la phase 1. Chaque revue de merge request vérifie les principes que la
modification touche. La complexité se justifie ; elle ne se constate pas.

**Guidance d'exécution.** Les conventions de travail au quotidien vivent dans le `CLAUDE.md` du
workspace et dans celui de chaque dépôt. Ils détaillent ce document sans le contredire ; là où ils
le contrediraient, ils sont faux et se corrigent.

**Version**: 1.0.0 | **Ratified**: 2026-09-17 | **Last Amended**: 2026-09-17
