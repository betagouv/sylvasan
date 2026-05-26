# 4. Organisation des composants et des pages Vue (web)

Date: 2026-05-26

## Statut

Accepté

## Contexte

L'application web utilise `unplugin-vue-router` pour le routage basé sur le système de fichiers : chaque fichier `.vue` présent dans `web/src/pages/` est automatiquement enregistré comme une route.

Initialement, certaines pages regroupaient leur fichier principal (`index.vue`) et leurs composants enfants dans un même dossier (ex. `pages/ResponseListPage/index.vue`, `pages/ResponseListPage/DateRangeFilter.vue`). Cette organisation présentait un problème : `unplugin-vue-router` détecte tous les fichiers `.vue` du dossier `pages/` comme des routes potentielles, y compris les composants qui n'ont pas vocation à être des pages. Le fichier `typed-router.d.ts` généré automatiquement se retrouvait alors pollué d'entrées parasites.

La convention de nommage avec préfixe `_` (underscore) ne permet plus d'exclure un fichier du routage automatique out-of-the-box. Il faudrait donc alourdir la configuration, les imports et dériver du comportement natif du routeur.

## Décision

- **`web/src/pages/`** ne contient que des fichiers plats (pas de sous-dossiers). Chaque fichier `.vue` dans ce dossier est une page à part entière.
- **`web/src/components/<NomDeLaPage>/`** accueille les composants utilisés exclusivement par une seule page (ex. `components/ResponseListPage/DateRangeFilter.vue`).
- **`web/src/components/`** (racine) accueille les composants partagés entre plusieurs pages.

## Conséquences

### Positives
- Le routage automatique fonctionne sans configuration supplémentaire ni convention de nommage spéciale.
- `typed-router.d.ts` reste propre et ne contient que de vraies routes.
- La colocalization des composants propres à une page est préservée via le dossier `components/<NomDeLaPage>/`.
- La frontière entre composants locaux et partagés est explicite et vérifiable à la lecture de l'arborescence.

### Négatives
- Un composant initialement local à une page nécessite un déplacement de dossier lorsqu'il devient partagé (de `components/MaPage/` vers `components/`).
- La relation entre une page et ses composants est visible dans le nom du dossier plutôt que par la proximité dans le système de fichiers.
