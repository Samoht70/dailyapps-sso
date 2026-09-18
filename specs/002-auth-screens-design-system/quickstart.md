# Quickstart — valider l'identité DailyApps sur le parcours

**Feature** : `002-auth-screens-design-system` | **Dépôt** : `api` seul

Ce document dit comment prouver que la feature est livrée. Il ne contient pas de code
d'implémentation — les tâches sont dans `tasks.md`.

---

## Prérequis

Session ouverte à la racine du workspace, jamais dans `api/`. Toute commande `artisan`,
`composer` ou de test passe par Sail.

```bash
cd api
composer install
npm install
./vendor/bin/sail up -d
./vendor/bin/sail artisan migrate
```

---

## 1. La suite passe, sans qu'un test ait été retouché

C'est SC-002, et c'est la première porte : la refonte est un habillage, pas une reprise de
comportement.

```bash
cd api
./vendor/bin/sail test
```

**Attendu** : tout au vert, y compris les tests neufs.

Puis la preuve qu'aucun test existant n'a été accommodé — les fichiers de test antérieurs à
la feature ne doivent apparaître **que** comme fichiers neufs, jamais comme fichiers
modifiés :

```bash
git -C api diff --stat staging -- 'technical/oidc/tests/**' 'functional/**/tests/**'
```

**Attendu** : uniquement des ajouts de fichiers. Une ligne de modification sur un test
antérieur fait échouer SC-002, quel que soit l'état du vert.

---

## 2. Les sept écrans répondent, et le 410 est toujours un 410

```bash
cd api
./vendor/bin/sail test --testsuite=technical/oidc
```

**Attendu** :

- les dix tests de `PasswordResetTest`, les huit d'`AcceptInvitationScreenTest`, les dix de
  `LoginScreenTest` et d'`AccountScreenTest` passent sans modification ;
- `it_answers_gone_for_an_expired_invitation`, `..._already_spent` et `..._nobody_issued`
  répondent toujours **410** — le corps a changé, pas le statut ;
- les tests neufs couvrent l'écran « invitation périmée » (statut 410 **et** message
  `oidc::screens.invitation.expired` présent) et l'état « lien de réinitialisation expiré »
  (statut 200, message `oidc::screens.reset_password.invalid`, action vers `password.forgot`).

---

## 3. Le socle de composants est réellement partagé

SC-001 : aucun écran ne définit un contrôle qui lui soit propre. Le test automatisé le
vérifie ; la commande ci-dessous en donne la lecture directe.

```bash
cd api
grep -nE '<(input|button|label|select|textarea)' technical/oidc/resources/views/livewire/*.blade.php
```

**Attendu** : aucune sortie. Les écrans ne composent que des `<x-oidc::…>`. Les seules
balises de formulaire brutes admises dans la couche vivent dans
`resources/views/components/`, où elles sont définies une fois.

```bash
grep -rnE '#[0-9a-fA-F]{6}|rgb\(' technical/oidc/resources/views/ | grep -v components/brand/
```

**Attendu** : aucune sortie. Toute couleur passe par un token ; seules les variantes du logo
portent des valeurs, parce qu'un SVG de marque en porte.

---

## 4. Le français et l'anglais disent la même chose

SC-004 se teste, et le test fait foi. Pour la lecture directe :

```bash
cd api
./vendor/bin/sail artisan tinker --execute '
$fr = require "technical/oidc/lang/fr/screens.php";
$en = require "technical/oidc/lang/en/screens.php";
$flat = function (array $a, string $p = "") use (&$flat): array {
    $out = [];
    foreach ($a as $k => $v) { $out = array_merge($out, is_array($v) ? $flat($v, "$p$k.") : ["$p$k"]); }
    return $out;
};
print_r(array_merge(array_diff($flat($fr), $flat($en)), array_diff($flat($en), $flat($fr))));
'
```

**Attendu** : un tableau vide.

---

## 5. Rien ne part vers un service extérieur

SC-006 et FR-008. La preuve est dans le paquet compilé, pas dans le code source.

```bash
cd api
npm run build
grep -rnE 'https?://(fonts\.|cdn\.|[a-z0-9.-]*googleapis|bunny\.net)' public/build/ resources/ technical/*/resources/
```

**Attendu** : aucune sortie. Les `@font-face` du paquet pointent vers
`public/build/assets/*.woff2`.

```bash
ls public/build/assets/ | grep -E 'lato|montserrat'
```

**Attendu** : les fichiers `lato-{300,400,700,900}-normal-*.woff2` et
`montserrat-700-normal-*.woff2`. Leur présence est ce qui prouve que les polices sont servies
par le produit.

Contre-épreuve au navigateur : onglet Réseau, filtre « Domaine », charger `/login` — aucune
requête hors de l'origine du produit.

---

## 6. Le parcours, à l'œil

Ce qui reste ne se teste pas en PHPUnit. À faire une fois, sur un navigateur, avec la
maquette ouverte à côté : https://claude.ai/artifact/6LzX3uK6QRvJm7WV1f5vVJ

```bash
cd api
./vendor/bin/sail artisan db:seed   # un compte et une organisation pour se connecter
npm run dev
```

| # | Chemin | À vérifier |
|---|---|---|
| 1 | `/login` | aplat noir, logo, accroche ; champs à 48 px ; bouton rouge pleine largeur |
| 2 | `/login`, identifiants faux | bandeau rouge **au-dessus** du formulaire, message inchangé, ne dit pas si le compte existe |
| 3 | `/password/forgot` | même aplat, même colonne ; après envoi, bandeau vert et lien de retour |
| 4 | lien de réinitialisation reçu par courriel | formulaire ; puis rouvrir le même lien après usage → écran « lien expiré » avec bouton d'action |
| 5 | lien d'invitation périmé | écran de marque, message d'invitation, **aucun bouton** — orientation vers l'administrateur |
| 6 | `/account` | barre haute avec logo sombre et déconnexion ; deux cartes ; **pas** de carte « Applications autorisées » |
| 7 | chacun des sept, fenêtre à 375 px | aucun défilement horizontal ; l'aplat cède la place, la marque reste visible |
| 8 | chacun des sept, navigation au clavier seul | l'anneau de focus est visible partout, l'ordre suit la lecture |

**SC-005** — la vérification qui donne son sens à la feature : placer quelqu'un devant
`/login` et devant une capture de l'écran d'avant (Tailwind brut, palette grise, sans
marque), et lui demander lequel est le vrai. La réponse doit être immédiate.

---

## 7. Avant de déclarer la feature finie

```bash
cd api && vendor/bin/pint --dirty --format agent
```

Puis, depuis la racine du workspace, le rapport qui fait foi :

```
/speckit-multirepo-status
```

**Attendu** : `api` sur `002-auth-screens-design-system`, rien de non commité, rien de non
poussé. `mobile` sur `staging`, intact — cette feature ne le touche pas. Le rapport se prend
au pied de la lettre ; un dépôt sur la mauvaise branche se traite avant toute autre chose.
