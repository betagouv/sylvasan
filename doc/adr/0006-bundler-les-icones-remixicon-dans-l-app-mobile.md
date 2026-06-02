# 6. Bundler les icônes RemixIcon dans l'application mobile

Date : 2026-06-02

## Statut

Accepté

## Contexte

L'application mobile utilise la bibliothèque `@iconify/vue` pour afficher les icônes RemixIcon (`ri:*`). Par défaut, Iconify résout les icônes en les téléchargeant à la demande depuis le CDN `api.iconify.design` au premier rendu du composant qui les référence.

Ce comportement posait deux problèmes dans le contexte Capacitor :

1. **Icônes absentes au premier lancement** : lors du premier démarrage, les icônes n'étaient pas encore en cache. Si la requête CDN échouait (réseau lent, hors-ligne, ou timeout dans la WebView), les icônes n'étaient jamais affichées, même après que l'appareil retrouve la connectivité (pas de retry automatique une fois le composant monté).

2. **Expiration du cache Iconify** : Iconify maintient un cache local (localStorage / sessionStorage) avec une TTL. Après expiration, les icônes doivent être re-téléchargées. Dans l'application mobile, ce re-téléchargement pouvait également échouer silencieusement dans les WebViews Android et iOS selon l'état du réseau au moment du lancement.

Le résultat visible : des icônes disparaissant de façon intermittente, en particulier après une réinstallation ou une longue période sans ouverture de l'application.

## Décision

Les icônes RemixIcon utilisées dans l'application sont intégrées statiquement dans le bundle JavaScript au moment de la compilation, via l'API `addCollection()` de `@iconify/vue`.

### Mécanisme

**1. Source de vérité : `mobile/scripts/icons.js`**

Ce fichier déclare manuellement la liste des icônes à inclure dans le bundle, sous la forme d'un tableau de noms d'icônes RemixIcon (sans le préfixe `ri-`). Il est passé en entrée à la CLI `vue-dsfr-icons` :

```js
import { icons } from "@iconify-json/ri"

export const collectionsToFilter = [
  [icons, ["calendar-line", "check-line", /* ... */]],
]
```

**2. Fichier généré : `mobile/src/icon-collections.ts`**

La CLI `vue-dsfr-icons` (fournie par `@gouvminint/vue-dsfr`) lit `scripts/icons.js` et génère `src/icon-collections.ts`, qui contient les données SVG inline de chaque icône ainsi qu'un objet `ri` de constantes typées :

```ts
const collections: IconifyJSON[] = [{ prefix: "ri", icons: { "check-line": { body: "..." }, ... } }]
export const ri = { checkLine: "ri:check-line", ... } as const
export default collections
```

**3. Enregistrement au démarrage : `mobile/src/main.ts`**

Avant le montage de l'application, toutes les collections sont enregistrées dans le registre global d'Iconify :

```ts
import { addCollection } from "@iconify/vue"
import collections from "./icon-collections"

for (const collection of collections) {
  addCollection(collection)
}
```

Iconify consulte ce registre en priorité avant toute requête réseau. Les icônes enregistrées sont disponibles de façon synchrone dès le premier rendu.

**4. Intégration dans le build**

Le script `npm run icons` est exécuté avant chaque compilation, garantissant que `icon-collections.ts` est toujours à jour :

```json
"icons": "vue-dsfr-icons -s scripts/icons.js -t src/icon-collections.ts",
"build": "npm run icons && vue-tsc -b && vite build"
```

`@iconify-json/ri` (la source SVG complète de RemixIcon) est une `devDependency` : les données sont extraites au moment du build et n'alourdissent pas le bundle runtime.

## Conséquences

### Positives

- Les icônes sont disponibles immédiatement au premier lancement, sans connexion réseau.
- Le comportement est déterministe et indépendant de l'état du cache Iconify.
- L'application fonctionne correctement en mode hors-ligne pour toutes les icônes déclarées.
- L'ajout d'icônes reste simple : modifier `scripts/icons.js` puis relancer `npm run icons`.

### Négatives

- **Maintenance manuelle** : chaque icône utilisée dans le code (y compris dans `shared/components/`) doit être déclarée explicitement dans `scripts/icons.js`. Un oubli entraîne une icône absente en production uniquement (le dev peut masquer le problème si le cache CDN est chaud).
- **Fichier généré commité** : `icon-collections.ts` est un artefact de build versionné. En l'absence d'un check CI qui vérifie la cohérence entre `scripts/icons.js` et `icon-collections.ts`, une divergence silencieuse est possible si un développeur ajoute une icône sans relancer `npm run icons`.
- **Surcharge de bundle légère** : les SVG des icônes déclarées sont inclus dans le JS principal. Pour une vingtaine d'icônes RemixIcon (~2 Ko gzip estimé), le coût est négligeable.

## Alternatives considérées

### Utiliser un composant d'icône différent (ex. `unplugin-icons`)

Remplacer `@iconify/vue` par un plugin Vite qui résout les icônes statiquement à la compilation via des imports. Rejeté : cela impliquerait de migrer tous les usages d'icônes dans `@gouvminint/vue-dsfr` (qui utilise `@iconify/vue` en interne), ce qui est hors scope.
