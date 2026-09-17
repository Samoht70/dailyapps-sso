# Feature Specification: Authentification centralisée (SSO) de l'écosystème DailyApps

**Feature Branch**: `001-sso-central-authentication`

**Created**: 2026-09-17

**Status**: Draft

**Input**: User description: "Je voudrais que cette application soit le point central de connexion de toutes mes applications, je veux une connexion en SSO. Je vais avoir à terme ~15 applications et elles doivent toutes passer par là pour se connecter, donc je ne sais pas si on fait un système d'OAuth, une page de login classique, plusieurs systèmes d'authentification. J'aurai des applications comme gestion de congés, de notes de frais, faire des covoiturages, carte de visite, c'est une liste non exhaustive. Mais j'aurai aussi une application de gestion des utilisateurs, des clients, des licences des applications : elle servira un peu de portail d'applications en gros, où je peux me rediriger sur n'importe quelle app que j'ai souscrite, donc je ne sais pas si elle fait doublon avec l'app de connexion."

**Arbitrages de cadrage** (réponses de l'auteur de la demande, 2026-09-17) :

- **Le portail ne fait pas doublon, et il n'est pas dans ce produit.** Le point central
  authentifie et détient les droits ; le portail et les écrans d'administration sont une
  application cliente distincte, raccordée comme les quatorze autres.
- **Un utilisateur appartient à une seule organisation cliente.**
- **Les comptes sont gérés par DailyApps.** Aucune fédération avec l'annuaire d'un client dans
  cette version.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Se connecter une seule fois, depuis n'importe quelle application (Priority: P1)

Un collaborateur d'une entreprise cliente ouvre le lien d'une application DailyApps — la gestion des
congés, par exemple. Il n'est pas encore identifié : l'application le renvoie vers l'écran de
connexion unique de DailyApps. Il saisit ses identifiants une fois, et revient exactement sur la page
qu'il visait, connecté. Plus tard dans la journée il ouvre les notes de frais : cette fois aucun écran
de connexion n'apparaît, il est déjà identifié et arrive directement dans l'application.

**Why this priority**: C'est la raison d'être du produit. Sans elle, chaque application refait sa
propre authentification et l'écosystème n'existe pas. C'est aussi le socle dont dépendent toutes les
autres histoires : les droits, la gouvernance et la révocation n'ont de sens qu'une fois la session
centrale établie.

**Independent Test**: Testable avec une seule application raccordée et un seul compte. On vérifie
qu'un accès non identifié aboutit à l'écran de connexion central, que l'identification renvoie sur la
page initialement demandée, et qu'une seconde application raccordée n'en redemande pas.

**Acceptance Scenarios**:

1. **Given** un utilisateur non identifié qui ouvre une URL protégée d'une application raccordée,
   **When** l'application constate l'absence de session, **Then** il est amené à l'écran de connexion
   central de DailyApps.
2. **Given** un utilisateur sur l'écran de connexion central arrivé depuis une page précise d'une
   application, **When** il s'identifie avec des identifiants valides, **Then** il revient sur cette
   page précise, identifié, sans étape supplémentaire.
3. **Given** un utilisateur déjà identifié auprès du point central, **When** il ouvre une seconde
   application raccordée à laquelle il a accès, **Then** il y entre sans ressaisir d'identifiants.
4. **Given** un utilisateur qui saisit des identifiants invalides, **When** il valide, **Then** il
   reste sur l'écran de connexion avec un message qui ne révèle pas si le compte existe.
5. **Given** un utilisateur identifié qui ouvre une application pour laquelle son organisation n'a pas
   de licence, **When** l'application interroge le point central, **Then** l'accès est refusé avec une
   explication distinguant « pas de licence » de « identifiants invalides ».
6. **Given** un utilisateur qui a oublié son mot de passe, **When** il demande sa réinitialisation,
   **Then** il reçoit un lien à usage unique et à durée limitée lui permettant d'en définir un nouveau.

---

### User Story 2 - Savoir à quoi un utilisateur a droit, sans qu'aucune application ne tienne son annuaire (Priority: P2)

Le portail d'applications affiche à l'utilisateur identifié la liste des applications qu'il peut
atteindre, et une application métier doit savoir quels rôles il y détient. Ni l'un ni l'autre ne
tiennent leur propre annuaire : ils posent la question au point central, qui répond en tenant compte
des licences de l'organisation, des accès attribués et de l'état du compte.

**Why this priority**: C'est ce qui transforme quinze applications séparées en un produit unique, et
ce qui évite que chaque application recopie les droits dans son coin — la dérive qui rend
ingouvernable un écosystème de cette taille. Vient après l'histoire 1, qui reste utilisable avec des
droits accordés à tous.

**Independent Test**: Testable avec deux applications déclarées et deux utilisateurs aux droits
différents, sans écrire le moindre écran : on interroge le point central pour chacun et on compare les
réponses aux droits attribués.

**Acceptance Scenarios**:

1. **Given** un utilisateur identifié dont l'organisation a souscrit trois applications et qui est
   rattaché à deux d'entre elles, **When** le point central est interrogé sur ses accès, **Then** il
   répond exactement ces deux applications.
2. **Given** un utilisateur identifié entrant dans une application, **When** celle-ci demande ses
   rôles, **Then** le point central répond les rôles détenus pour cette application et pour elle seule.
3. **Given** un administrateur qui vient d'accorder un accès à un utilisateur, **When** le point
   central est réinterrogé, **Then** la nouvelle application figure dans la réponse.
4. **Given** un utilisateur dont l'organisation n'a aucune licence valide, **When** le point central
   est interrogé, **Then** il répond une liste vide, distinctement d'une erreur.
5. **Given** une application qui interroge le point central sur un utilisateur, **When** elle demande
   des informations qui ne la concernent pas — les rôles d'un tiers, les accès sur une autre
   application, **Then** la demande est refusée.

---

### User Story 3 - Gouverner les organisations, les licences et les accès (Priority: P2)

Un administrateur DailyApps déclare une entreprise cliente, lui attribue les licences des
applications qu'elle a souscrites, avec leur période de validité et leur nombre de sièges. Un
administrateur côté client gère ensuite ses propres collaborateurs : il en invite, leur donne accès
aux applications couvertes par ses licences, et retire cet accès quand quelqu'un change de poste ou
quitte l'entreprise. Ils travaillent depuis l'application d'administration ; ce que ce produit livre,
ce sont les opérations, les règles et les données que cette application manipule.

**Why this priority**: Sans cette gouvernance, tout accès se crée à la main et l'écosystème ne
dépasse pas la démonstration. Elle vient après le SSO lui-même parce qu'un jeu de données créé
directement suffit à faire fonctionner et à démontrer les histoires 1 et 2.

**Independent Test**: Testable sans aucun écran, en enchaînant les opérations exposées : créer une
organisation, une licence, un utilisateur, lui accorder puis lui retirer un accès, et constater à
chaque étape le changement dans ce que le point central répond sur ses droits.

**Acceptance Scenarios**:

1. **Given** un administrateur DailyApps, **When** il déclare une organisation cliente et lui attribue
   la licence d'une application avec une date de fin, **Then** cette application devient attribuable
   aux utilisateurs de cette organisation.
2. **Given** une licence dont le nombre de sièges est atteint, **When** un administrateur client tente
   d'y rattacher un utilisateur de plus, **Then** l'opération est refusée avec un message indiquant la
   limite atteinte.
3. **Given** une licence arrivée à échéance, **When** un utilisateur de l'organisation tente
   d'atteindre l'application concernée, **Then** l'accès est refusé, alors que ses autres applications
   restent accessibles.
4. **Given** un administrateur client, **When** il invite un nouveau collaborateur, **Then** celui-ci
   reçoit une invitation lui permettant de définir son mot de passe et d'accéder aux applications
   qu'on lui a attribuées.
5. **Given** un administrateur client, **When** il tente d'atteindre les utilisateurs, les licences ou
   les accès d'une autre organisation, **Then** l'opération est refusée.
6. **Given** une organisation n'ayant qu'un seul administrateur actif, **When** on tente de le
   désactiver ou de lui retirer son rôle, **Then** l'opération est refusée.

---

### User Story 4 - Raccorder une nouvelle application à l'écosystème (Priority: P3)

L'écosystème passe de quelques applications à une quinzaine sur plusieurs années. Un administrateur
DailyApps déclare la nouvelle application : son nom, son logo, son adresse, les adresses de retour
autorisées et les rôles qu'elle expose. Elle devient immédiatement raccordable et peut être vendue à
une organisation — sans modifier ni redéployer le point central, ni aucune des applications déjà en
place.

**Why this priority**: Indispensable à terme, mais les premières applications peuvent être déclarées
directement. La valeur de cette histoire apparaît quand le rythme d'ajout s'accélère.

**Independent Test**: Testable en déclarant une application factice et en constatant qu'elle peut
mener une connexion à son terme sans aucune intervention sur le point central.

**Acceptance Scenarios**:

1. **Given** un administrateur DailyApps, **When** il déclare une application avec ses adresses de
   retour autorisées, **Then** cette application peut immédiatement faire identifier ses utilisateurs
   par le point central.
2. **Given** une application déclarée, **When** une demande de connexion arrive avec une adresse de
   retour absente de la liste autorisée, **Then** la demande est rejetée et l'utilisateur n'est jamais
   renvoyé vers cette adresse.
3. **Given** une application retirée du catalogue, **When** le point central est interrogé sur les
   accès d'un utilisateur qui la détenait, **Then** elle ne figure plus dans la réponse, sans que
   l'historique de ses accès passés soit perdu.
4. **Given** une application dont le moyen d'authentification est révoqué, **When** elle s'adresse au
   point central, **Then** elle est rejetée, sans effet sur les autres applications raccordées.

---

### User Story 5 - Fermer une session partout, couper un accès tout de suite (Priority: P3)

Un utilisateur se déconnecte depuis n'importe laquelle des applications : sa session centrale se
ferme, et les autres applications ouvertes ne le reconnaissent plus. Symétriquement, quand un
administrateur désactive un compte — un départ, un poste perdu, un soupçon de compromission —
l'accès est coupé partout sans attendre l'expiration naturelle des sessions en cours.

**Why this priority**: Un point d'authentification unique concentre le risque : une session qui
survit à une désactivation vaut pour les quinze applications à la fois. Priorité basse uniquement
parce qu'une durée de session courte limite la fenêtre d'exposition en attendant.

**Independent Test**: Testable avec deux applications ouvertes simultanément. On se déconnecte depuis
l'une et on vérifie l'autre ; puis on désactive un compte pendant qu'il a des sessions ouvertes et on
vérifie le délai de coupure.

**Acceptance Scenarios**:

1. **Given** un utilisateur identifié avec deux applications ouvertes, **When** il se déconnecte depuis
   l'une, **Then** l'autre ne le reconnaît plus à l'action suivante.
2. **Given** un utilisateur avec des sessions actives, **When** un administrateur désactive son compte,
   **Then** son accès est refusé partout dans le délai annoncé, sans qu'il ait à se déconnecter.
3. **Given** un utilisateur qui change son mot de passe, **When** le changement est confirmé,
   **Then** ses autres sessions ouvertes sont fermées.
4. **Given** un utilisateur inactif au-delà de la durée de session, **When** il revient sur une
   application, **Then** il doit se réidentifier.
5. **Given** une licence résiliée pendant qu'un utilisateur travaille dans l'application concernée,
   **When** il poursuit son activité, **Then** l'accès lui est coupé sans attendre sa reconnexion.

---

### Edge Cases

- **Panne du point central** : toutes les applications deviennent inaccessibles en même temps. Que
  voit un utilisateur, et que fait une application qui n'arrive pas à joindre le point central ?
- **Licence résiliée ou expirée pendant une session active** : l'accès doit tomber sans attendre la
  prochaine connexion.
- **Adresse électronique déjà connue** : la même personne invitée par une deuxième organisation. Le
  rattachement étant unique, cette invitation doit être refusée explicitement plutôt que de créer un
  compte fantôme ou de déplacer silencieusement la personne.
- **Adresse de retour non déclarée** dans une demande de connexion : la demande est rejetée sans
  redirection, sinon le point central sert de tremplin vers un site tiers.
- **Retour en arrière du navigateur** sur l'écran de connexion après identification, ou soumission
  deux fois du même formulaire.
- **Deux onglets, deux applications, une déconnexion** : le second onglet doit cesser d'être utilisable.
- **Compte administrateur unique désactivé par erreur** : une organisation ne doit pas pouvoir se
  retrouver sans aucun administrateur.
- **Tentatives répétées d'identification** sur un même compte ou depuis une même origine.
- **Utilisateur sans aucun accès attribué** : le point central répond une liste vide, ce qui doit se
  distinguer d'une erreur pour que le portail puisse l'expliquer.
- **Lien d'invitation ou de réinitialisation réutilisé, expiré, ou remplacé** par une demande plus
  récente.
- **Organisation suspendue** : tous ses utilisateurs perdent l'accès, y compris ses administrateurs.

## Requirements *(mandatory)*

### Functional Requirements

#### Identification et session

- **FR-001**: Le système MUST proposer un unique écran de connexion, partagé par toutes les
  applications de l'écosystème ; aucune application ne collecte elle-même les identifiants.
- **FR-002**: Le système MUST permettre à une application de faire identifier un visiteur puis de le
  recevoir en retour, avec son identité et ses droits sur cette application.
- **FR-003**: Le système MUST ramener l'utilisateur, après identification, sur la page qu'il visait
  initialement, y compris quand il s'agit d'un lien profond dans l'application.
- **FR-004**: Le système MUST n'exiger qu'une seule identification tant que la session centrale est
  valide, quel que soit le nombre d'applications ouvertes.
- **FR-005**: Le système MUST authentifier par adresse électronique et mot de passe, gérés par
  DailyApps et par lui seul.
- **FR-006**: Le système MUST refuser une demande de connexion dont l'adresse de retour ne figure pas
  parmi celles déclarées pour l'application, et ne jamais rediriger vers une adresse non déclarée.
- **FR-007**: Le système MUST répondre à un échec d'identification par un message identique que le
  compte existe ou non.
- **FR-008**: Le système MUST limiter les tentatives d'identification répétées sur un même compte et
  depuis une même origine, et journaliser les blocages.
- **FR-009**: Le système MUST imposer une exigence minimale de robustesse au mot de passe et refuser
  celui qui ne la satisfait pas, en disant pourquoi.
- **FR-010**: Le système MUST fermer la session au terme d'une durée d'inactivité et d'une durée
  absolue, toutes deux configurables.
- **FR-011**: Le système MUST permettre à un utilisateur de réinitialiser son mot de passe seul, par
  un lien à usage unique et à durée limitée envoyé à son adresse électronique.
- **FR-012**: Le système MUST fermer toutes les sessions ouvertes d'un utilisateur lorsque son mot de
  passe change.
- **FR-013**: Le système MUST permettre à un utilisateur de consulter et de modifier son propre profil
  et son mot de passe, sans passer par un administrateur.

#### Droits exposés aux applications

- **FR-014**: Le système MUST répondre, pour un utilisateur identifié, la liste des applications qu'il
  peut atteindre — celles dont son organisation détient une licence valide et auxquelles il est
  rattaché — afin qu'un portail puisse la présenter sans tenir son propre annuaire.
- **FR-015**: Le système MUST accompagner chaque application de cette liste des éléments nécessaires
  à son affichage et à son lancement : nom, logo, adresse.
- **FR-016**: Le système MUST transmettre à une application, au moment de l'identification, les rôles
  que l'utilisateur détient sur elle, et sur elle seule.
- **FR-017**: Le système MUST refuser à une application toute demande portant sur un périmètre qui
  n'est pas le sien — les droits d'un utilisateur sur une autre application, les données d'une autre
  organisation.
- **FR-018**: Le système MUST distinguer, dans ses réponses, l'absence de droits d'une erreur de
  traitement.
- **FR-019**: Le système MUST refléter toute modification de droits dans la réponse suivante, sans
  délai imposé par une mise en cache.

#### Organisations, licences et accès

- **FR-020**: Le système MUST permettre de déclarer une organisation cliente, de la modifier, de la
  suspendre et de la réactiver.
- **FR-021**: Le système MUST couper l'accès de tous les utilisateurs d'une organisation suspendue, y
  compris celui de ses administrateurs.
- **FR-022**: Le système MUST permettre d'attribuer à une organisation la licence d'une application,
  avec une période de validité et un nombre de sièges.
- **FR-023**: Le système MUST refuser tout accès d'un utilisateur à une application dont l'organisation
  n'a pas de licence valide, et appliquer ce refus aux sessions déjà ouvertes.
- **FR-024**: Le système MUST refuser le rattachement d'un utilisateur de plus lorsque le nombre de
  sièges d'une licence est atteint, en indiquant la limite.
- **FR-025**: Le système MUST rattacher chaque utilisateur à exactement une organisation cliente.
- **FR-026**: Le système MUST refuser l'invitation d'une adresse électronique déjà rattachée à une
  organisation, en l'énonçant explicitement.
- **FR-027**: Le système MUST permettre d'inviter un utilisateur, de lui attribuer et de lui retirer
  des accès applicatifs, de le désactiver et de le réactiver.
- **FR-028**: Le système MUST restreindre un administrateur client à sa seule organisation, pour toute
  lecture comme pour toute écriture.
- **FR-029**: Le système MUST empêcher qu'une organisation se retrouve sans aucun administrateur actif.
- **FR-030**: Le système MUST permettre d'attribuer à un utilisateur, pour chaque application à
  laquelle il a accès, les rôles que cette application expose.

#### Cycle de vie des applications

- **FR-031**: Le système MUST permettre de déclarer une nouvelle application — nom, logo, adresse,
  adresses de retour autorisées, rôles exposés — sans modification ni redéploiement du point central.
- **FR-032**: Le système MUST permettre de retirer une application du catalogue, ce qui la fait
  disparaître des droits répondus sans supprimer l'historique des accès passés.
- **FR-033**: Le système MUST donner à chaque application déclarée un moyen de s'authentifier auprès
  du point central, révocable et renouvelable sans intervention sur les autres applications.

#### Fin de session et révocation

- **FR-034**: Le système MUST permettre une déconnexion déclenchée depuis n'importe quelle application
  et qui ferme la session centrale.
- **FR-035**: Le système MUST rendre les autres applications ouvertes inutilisables après cette
  déconnexion, à leur prochaine interaction.
- **FR-036**: Le système MUST couper l'accès d'un compte désactivé à toutes les applications dans le
  délai annoncé, sans attendre l'expiration naturelle de ses sessions.

#### Traçabilité

- **FR-037**: Le système MUST journaliser les événements de sécurité — identification réussie ou
  échouée, déconnexion, changement de mot de passe, attribution ou retrait d'accès, désactivation de
  compte, déclaration ou retrait d'application, révocation d'un moyen d'authentification — avec leur
  auteur, leur horodatage et leur origine.
- **FR-038**: Le système MUST exposer ces événements à un administrateur pour son seul périmètre, de
  quoi répondre à la question « qui a eu accès à quoi, et depuis quand ».
- **FR-039**: Le système MUST conserver ces journaux au moins douze mois.

### Key Entities *(include if feature involves data)*

- **Utilisateur** : une personne, une identité unique à l'échelle de l'écosystème, identifiée par son
  adresse électronique. Porte son état — invité, actif, désactivé — et son mot de passe. Rattaché à
  exactement une organisation.
- **Organisation cliente** : l'entreprise qui souscrit aux applications. Porte les licences, son état
  — active, suspendue — et délimite ce qu'un administrateur client peut atteindre.
- **Rattachement** : le lien entre un utilisateur et son organisation, avec son rôle dans celle-ci
  (membre, administrateur).
- **Application** : une application de l'écosystème. Porte son nom, son logo, son adresse, ses
  adresses de retour autorisées, les rôles qu'elle expose, son moyen d'authentification et son état au
  catalogue.
- **Licence** : le droit d'une organisation à utiliser une application, sur une période et pour un
  nombre de sièges donnés.
- **Accès applicatif** : l'attribution d'une application à un utilisateur, consommant un siège de la
  licence, avec les rôles qu'il y détient.
- **Session** : l'identification en cours d'un utilisateur auprès du point central, avec sa date de
  début, son échéance et les applications qui s'y adossent.
- **Invitation** : une proposition de rattachement à durée limitée et à usage unique, adressée à une
  adresse électronique.
- **Événement de sécurité** : une trace horodatée et attribuée d'une action sensible.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un utilisateur saisit ses identifiants au plus une fois par journée de travail, quel que
  soit le nombre d'applications qu'il utilise ce jour-là.
- **SC-002**: Passer d'une application à une autre prend moins de 5 secondes et aucune saisie.
- **SC-003**: Une première connexion, de l'arrivée sur l'écran jusqu'au retour dans l'application,
  aboutit en moins de 30 secondes pour un utilisateur qui connaît ses identifiants.
- **SC-004**: Raccorder une application supplémentaire ne demande aucune modification du point central
  ni des applications déjà raccordées, et se fait en moins d'une journée ouvrée.
- **SC-005**: Désactiver un compte lui coupe l'accès à 100 % des applications en moins d'une minute.
- **SC-006**: Le point central est disponible 99,9 % du temps sur un mois glissant, sachant qu'une
  indisponibilité rend les quinze applications inaccessibles.
- **SC-007**: L'écosystème supporte 15 applications raccordées et 2 000 utilisateurs identifiés
  simultanément sans dégradation perceptible du temps de connexion.
- **SC-008**: 95 % des utilisateurs atteignent l'application visée dès leur première tentative, sans
  aide.
- **SC-009**: Un administrateur répond à la question « quelles applications cette personne peut-elle
  atteindre, et qui le lui a accordé » en moins de 2 minutes, sans intervention technique.
- **SC-010**: Une application raccordée ne conserve aucune liste d'utilisateurs ni de droits qui lui
  soit propre : 100 % des décisions d'accès s'appuient sur la réponse du point central.
- **SC-011**: Le nombre de demandes d'assistance liées aux mots de passe et aux comptes multiples
  diminue d'au moins 50 % par rapport à la situation où chaque application gère ses propres comptes.

## Assumptions

- **Le point central est le seul détenteur des identifiants.** Aucune application de l'écosystème ne
  stocke de mot de passe ni ne propose son propre écran de connexion.
- **Le portail et l'administration sont hors périmètre.** Ce produit détient les données et les règles
  — organisations, licences, applications, accès — et les expose ; les écrans qui les manipulent
  appartiennent à une application cliente distincte, qui aura sa propre spécification. Ce produit ne
  livre que ses écrans à lui : connexion, invitation, mot de passe oublié, profil.
- **Le modèle est multi-organisations (B2B).** « Client » désigne une entreprise cliente qui souscrit
  des licences, et non l'utilisateur final.
- **Un utilisateur appartient à une seule organisation.** Le cas du prestataire travaillant pour deux
  clients se traite par deux comptes et deux adresses électroniques distinctes. L'ouvrir plus tard
  serait une reprise de données lourde, assumée comme telle.
- **Les applications sont des applications web et mobiles construites en interne.** Le raccordement
  d'un logiciel du marché imposant son propre protocole n'est pas pris en compte.
- **Les rôles sont définis par chaque application et attribués depuis le point central.** Le point
  central transporte les rôles mais n'arbitre pas les règles métier internes à une application.
- **Une application interrogée par un utilisateur sans accès affiche un refus explicite** plutôt que
  de le renvoyer à l'écran de connexion, ce qui serait illisible.
- **L'authentification à plusieurs facteurs n'est pas dans le périmètre de la première version.**
  Elle reste un besoin attendu d'un point d'authentification d'entreprise et devra faire l'objet de sa
  propre spécification.
- **La fédération avec l'annuaire d'un client n'est pas dans le périmètre.** Elle deviendra un besoin
  dès qu'un client d'une certaine taille l'exigera, et fera alors l'objet de sa propre spécification.
- **La reprise de comptes existants dans des applications déjà en production n'est pas dans le
  périmètre.** Les applications citées — congés, notes de frais, covoiturage, carte de visite — sont
  supposées à construire ou à raccorder sans historique de comptes à migrer.
- **La facturation des licences n'est pas dans le périmètre.** Le système enregistre ce qu'une
  organisation a le droit d'utiliser, pas ce qu'elle doit payer.
- **Le workspace est vierge de toute fonctionnalité.** Ce qui existe n'est qu'un échafaudage : rien
  n'est à reprendre, tout est à construire.
- **L'application mobile ne porte aucun écran dans cette feature.** Un point d'authentification n'a
  pas d'application native propre ; le dépôt mobile attend la première application métier, ou une
  décision contraire au moment du plan.
- **Un compte d'administration DailyApps existera dès l'installation** afin d'amorcer la première
  organisation et la première application, sans quoi le système ne peut pas démarrer.
