# Feature Specification: Identité DailyApps sur le parcours d'authentification

**Feature Branch**: `002-auth-screens-design-system`

**Created**: 2026-09-18

**Status**: Draft

**Input**: User description: "Habiller les écrans d'authentification de DailyApps SSO avec l'identité DailyApps, et compléter le parcours par l'écran qui manque."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Un parcours d'authentification qui porte la marque (Priority: P1)

Un salarié ouvre l'écran de connexion de DailyApps depuis n'importe quelle application de
la suite. Il reconnaît immédiatement à qui il confie son mot de passe : la marque est là,
la mise en page est la même d'un écran à l'autre, et les champs, boutons et messages se
ressemblent partout. Qu'il se connecte, demande un nouveau mot de passe, active son compte
ou modifie son profil, il a le sentiment d'être resté au même endroit.

**Why this priority**: c'est la porte d'entrée de tout l'écosystème, et aujourd'hui elle
n'est reliée à aucune marque. Un écran d'authentification anonyme est le terrain de jeu du
hameçonnage : un utilisateur qui ne sait pas reconnaître le vrai écran ne peut pas repérer
le faux. C'est aussi le lot qui n'attend aucune décision produit — il livre la valeur
entière pour les cinq écrans existants.

**Independent Test**: parcourir les cinq écrans existants et vérifier qu'ils partagent
palette, typographie et contrôles, que la marque est présente sur chacun, et que leur
comportement — validations, redirections, messages — est strictement inchangé.

**Acceptance Scenarios**:

1. **Given** un visiteur non authentifié, **When** il ouvre l'écran de connexion, **Then**
   l'écran porte la marque DailyApps et les couleurs, la typographie et les contrôles de
   l'identité retenue.
2. **Given** un visiteur sur l'écran de connexion, **When** il soumet des identifiants
   erronés, **Then** le message d'échec reste celui d'aujourd'hui, ne révèle pas si le
   compte existe, et s'affiche dans le style d'erreur commun à tous les écrans.
3. **Given** un utilisateur authentifié, **When** il ouvre son profil, **Then** l'écran
   emploie les mêmes composants que les écrans d'entrée, dans une mise en page de page
   connectée.
4. **Given** n'importe quel écran du parcours, **When** il est consulté sur un écran de
   téléphone, **Then** son contenu reste lisible et utilisable sans défilement horizontal.
5. **Given** la suite de tests existante, **When** elle est relancée après la refonte,
   **Then** elle passe intégralement, sans qu'aucun test ait été modifié pour l'accommoder.

---

### User Story 2 - Une sortie de secours quand le lien n'est plus valable (Priority: P2)

Un salarié clique sur un lien de réinitialisation reçu la semaine dernière, ou sur une
invitation périmée. Plutôt qu'un message sec ou une page vide, il comprend ce qui s'est
passé et ce qu'il peut faire : redemander un lien lui-même quand c'est en son pouvoir,
s'adresser à son administrateur quand ça ne l'est pas.

**Why this priority**: c'est la seule impasse du parcours que l'utilisateur atteint sans
avoir rien fait de mal, simplement parce que le temps a passé. Les textes existent déjà
dans les fichiers de traduction, mais aucun écran ne les porte. Le lot est petit et
indépendant.

**Independent Test**: ouvrir un lien de réinitialisation périmé puis une invitation
périmée, et vérifier que chaque cas affiche son propre message et sa propre action.

**Acceptance Scenarios**:

1. **Given** un lien de réinitialisation qui n'est plus valable, **When** l'utilisateur
   l'ouvre, **Then** il voit une explication et peut demander un nouveau lien sans passer
   par quelqu'un d'autre.
2. **Given** une invitation qui n'est plus valable, **When** l'utilisateur l'ouvre,
   **Then** il voit une explication et est orienté vers l'administrateur de son
   organisation, sans qu'aucune action hors de sa portée ne lui soit proposée.
3. **Given** l'un ou l'autre de ces écrans, **When** il s'affiche, **Then** les textes
   proviennent des libellés déjà traduits.

---

### Edge Cases

- Que se passe-t-il quand un lien de réinitialisation a déjà servi, par opposition à un
  lien simplement périmé ? Les deux cas mènent-ils au même écran ?
- Comment la mise en page scindée — aplat de marque et formulaire côte à côte — se
  comporte-t-elle sur un écran étroit ?
- Que devient l'affichage quand un message d'erreur de validation et un message d'échec
  d'authentification apparaissent en même temps sur le même écran ?
- Un utilisateur qui a désactivé le chargement des polices distantes voit-il un écran
  encore lisible et correctement espacé ?

## Requirements *(mandatory)*

### Functional Requirements

#### Identité et socle commun

- **FR-001**: Le parcours d'authentification MUST présenter une identité visuelle unique —
  mêmes couleurs, même typographie, mêmes formes de contrôle — sur la totalité de ses
  écrans.
- **FR-002**: Chaque écran du parcours MUST porter la marque DailyApps de manière
  identifiable sans lecture, afin qu'un utilisateur puisse distinguer l'écran authentique
  d'une imitation.
- **FR-003**: Les contrôles de formulaire — champ de saisie, bouton, case à cocher, message
  d'erreur, message de succès, carte de contenu — MUST être définis une seule fois et
  réutilisés par tous les écrans, aucun écran ne redéfinissant les siens.
- **FR-004**: Le comportement fonctionnel des cinq écrans existants MUST rester strictement
  inchangé : mêmes règles de validation, mêmes redirections, mêmes messages, mêmes
  protections contre les tentatives répétées.
- **FR-005**: Tout texte présenté à un utilisateur MUST provenir des fichiers de traduction,
  et tout texte nouveau MUST exister en français et en anglais.
- **FR-006**: Les écrans MUST rester lisibles et utilisables depuis un téléphone comme
  depuis un poste de travail, sans défilement horizontal.
- **FR-007**: Le contraste entre un texte et son fond MUST atteindre au moins 4,5:1, ramené
  à 3:1 au-delà de 24 px.
- **FR-008**: L'affichage des écrans NE DOIT PAS dépendre d'un service extérieur au moment
  où ils s'affichent : les ressources de l'identité — polices, marque — MUST être servies
  par le produit lui-même.

#### Sorties de secours

- **FR-009**: Quand un lien de réinitialisation n'est plus valable, le système MUST
  l'expliquer à l'utilisateur et lui permettre de demander un nouveau lien par lui-même.
- **FR-010**: Quand une invitation n'est plus valable, le système MUST l'expliquer et
  orienter l'utilisateur vers l'administrateur de son organisation, sans lui proposer
  d'action qu'il ne peut pas accomplir.
- **FR-011**: Ces écrans MUST réutiliser les libellés d'invalidité déjà traduits plutôt
  que d'en introduire de nouveaux.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Les sept écrans du parcours partagent la même palette, la même typographie et
  le même jeu de contrôles ; aucun écran ne définit un contrôle qui lui soit propre.
- **SC-002**: La totalité des tests couvrant le parcours d'authentification passe après la
  refonte, sans qu'aucun ait été modifié pour l'accommoder.
- **SC-003**: Un utilisateur arrivant avec un lien périmé dispose, sur le même écran, de
  l'explication et de la suite à donner — action directe quand elle est en son pouvoir,
  interlocuteur nommé sinon.
- **SC-004**: Chaque texte affiché par le parcours existe en français et en anglais.
- **SC-005**: Un utilisateur placé devant l'écran d'authentification et devant une imitation
  sans marque distingue le premier du second.
- **SC-006**: Aucun écran du parcours ne sollicite un service extérieur pour s'afficher.

## Assumptions

- L'identité visuelle n'est pas à créer : elle reprend telle quelle celle du XEFI Design
  System, déjà arbitrée et partagée au niveau de l'organisation. La maquette validée sert de
  référence — https://claude.ai/artifact/6LzX3uK6QRvJm7WV1f5vVJ
- Le périmètre est le dépôt `api` seul. L'application mobile n'est pas concernée par cette
  feature.
- Les cinq écrans existants sont fonctionnels et testés ; cette feature les habille sans
  toucher à leur logique.
- Les polices retenues par l'identité ne sont pas toutes fournies par le design system :
  celles qui manquent devront être approvisionnées et servies par le produit.
- Le thème sombre prévu par le design system n'entre pas dans cette feature.
- L'écran de profil est habillé tel qu'il existe aujourd'hui. La section « Applications
  autorisées » que montre la maquette relève de la feature 003 et n'est pas livrée ici.
- Le socle de composants livré par la user story 1 est dimensionné pour servir aussi les
  écrans de la feature 003, mais aucun écran de cette feature n'est construit ici.

## Hors périmètre

Le parcours d'autorisation des applications tierces — consentement, reprise d'un accès,
désignation de l'organisation, refus qui ne repassent pas par l'application appelante —
formait initialement une troisième user story de cette feature. Il en a été extrait le
2026-09-18, après lecture du contrat d'intégration du Xefi Store, parce qu'il constitue un
lot cohérent qui dépend de décisions protocolaires et non de l'habillage. Il fait l'objet de
la **feature 003**.

Ce découpage a une conséquence assumée : si la feature 003 retient le marquage de la page de
connexion aux couleurs de l'organisation appelante, l'aplat de marque livré ici sera repris.
Le socle de composants, lui, ne bouge pas.
