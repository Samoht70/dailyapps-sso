# Specification Quality Checklist: Authentification centralisée (SSO) de l'écosystème DailyApps

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-17
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

**Itération 1** — deux cases en échec, toutes deux suspendues aux trois marqueurs
`[NEEDS CLARIFICATION]` : moyens d'authentification au lancement, appartenance du
portail au produit, rattachement mono- ou multi-organisation. Une fuite de détail
d'implémentation dans les hypothèses (noms des frameworks des trois dépôts) a été
corrigée au même passage.

**Itération 2** — les trois questions ont été tranchées par l'auteur de la demande :
portail et administration hors périmètre, rattachement unique à une organisation,
comptes gérés par DailyApps sans fédération. La spécification a été réécrite en
conséquence : l'histoire du portail est devenue « exposer les droits » (US2), les
écrans d'administration sont sortis du périmètre au profit des opérations et des
règles que ce produit détient, et les hypothèses énoncent désormais ce que ce
produit ne livre pas. Les dix-huit cases passent.

**Deux points laissés en hypothèse plutôt qu'en question**, à confirmer au plan :

- Le dépôt mobile ne porte aucun écran dans cette feature — un point
  d'authentification n'a pas d'application native propre.
- L'authentification à plusieurs facteurs et la fédération d'annuaire sont hors
  périmètre de la v1 ; l'une comme l'autre sont des besoins attendus d'un point
  d'authentification d'entreprise et auront leur propre spécification.

**Révision du 2026-09-17, après `/speckit-plan`** — deux corrections descendues de la phase de plan :

- L'hypothèse « les trois dépôts du workspace » est devenue fausse. Le dépôt `front` (Nuxt) a été
  retiré : le portail et l'administration étant hors périmètre, il ne lui restait que cinq
  formulaires, désormais servis en Livewire par la même application que `/oauth/authorize`.
  L'hypothèse a été reformulée sans compter les dépôts, ce qui la met aussi à l'abri du prochain
  changement de découpage.
- La spécification reste exempte de nom de stack : elle ne mentionnait ni Nuxt ni Livewire, et ce
  changement de structure ne l'a donc pas touchée ailleurs. C'était le but de la case
  `No implementation details`.

Les dix-huit cases restent passantes.
