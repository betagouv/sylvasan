# 7. Injection de capacités spécifiques à la plateforme dans FieldRenderer par prop-drilling

Date : 2026-06-24

## Statut

Accepté

## Contexte

Les composants de rendu de formulaire (`SurveyRenderer`, `FieldRenderer`, `ImagesField`, etc.) vivent dans `shared/components/` pour être réutilisés à la fois dans l'application web et l'application mobile. Cette mutualisation implique que ces composants ne peuvent pas dépendre directement de bibliothèques natives comme `@capacitor/filesystem` ou `@capacitor/google-maps`.

Certains champs nécessitent pourtant des comportements qui n'ont de sens que sur une plateforme ou l'autre :

- **Champ carte** (`widget: "map"`) : le rendu cartographique repose sur des technologies différentes sur web et sur mobile.
- **Champ image** (`widget: "image"`) : l'affichage d'une image stockée en brouillon local nécessite `Filesystem.getUri()` pour obtenir l'URI native absolue, puis `Capacitor.convertFileSrc()` pour la traduire en URL accessible par la WebView. Ces deux appels sont propres à Capacitor et ne peuvent pas figurer dans un composant partagé.

## Décision

Les capacités spécifiques à la plateforme sont injectées dans la chaîne de composants partagés via des **props optionnelles**. Les composants partagés ignorent l'implémentation concrète — ils reçoivent soit un composant Vue, soit une fonction — et se contentent de les appeler si elles sont présentes. Le web et le mobile fournissent ces props à `SurveyRenderer`, qui les propage à `FieldRenderer`, qui les transmet aux composants de champ concernés.

Deux props suivent ce pattern à ce jour :

- `mobile/src/utils/imageStorage.ts` expose `resolveLocalImageSrc`, qui appelle `Filesystem.getUri()` puis `convertFileSrc()`.
- `mobile/src/components/MapField.vue` encapsule le rendu cartographique spécifique à chaque plateforme.

## Alternatives considérées

### Imports dynamiques dans les composants partagés

Utiliser `await import("@capacitor/filesystem")` dans `ImagesField.vue` au moment où la résolution est nécessaire.

Rejeté : même si le build web ne casse pas grâce au `try/catch`, le composant partagé acquiert une connaissance implicite de Capacitor. Cela viole la séparation des responsabilités et rend les composants partagés plus difficiles à tester en dehors du contexte mobile.

### Provide / inject

Fournir les capacités via `provide()` dans `SurveyPage.vue` et les consommer via `inject()` dans les composants de feuille.

Écarté pour ce cas : le prop-drilling explicite offre une meilleure traçabilité (les props sont visibles dans les signatures de composants et dans les DevTools Vue) et évite le couplage implicite qu'introduit un `inject` sans garantie de présence de la valeur. La chaîne de transmission n'est que de trois niveaux (`SurveyPage` → `SurveyRenderer` → `FieldRenderer` → composant de champ), ce qui reste gérable. Si la chaîne devait s'allonger significativement, `provide/inject` redeviendrait pertinent.

### Composants de rendu distincts par plateforme

Dupliquer `FieldRenderer` en une version web et une version mobile, la version mobile important directement les dépendances Capacitor.

Rejeté : la logique de rendu des champs (conditions d'affichage, validation, gestion du modèle) est identique sur les deux plateformes. La duplication crée un risque de divergence et double la surface de maintenance pour des différences qui se résument à quelques props optionnelles.

## Conséquences

### Positives

- Les composants dans `shared/` restent agnostiques à la plateforme et testables sans environnement Capacitor.
- L'ajout d'une nouvelle capacité mobile se fait en ajoutant une prop optionnelle à `FieldRenderer` (et en la propageant dans `SurveyRenderer`) : le pattern est établi et prévisible.
- Les DevTools Vue montrent explicitement quelles capacités sont injectées dans l'arbre de composants.

### Négatives

- Chaque nouvelle capacité mobile nécessite d'ajouter la prop à `SurveyRenderer` et `FieldRenderer`, même s'ils ne l'utilisent pas directement — ils ne font que la transmettre.
- Si le nombre de capacités injectées venait à croître (> 4-5 props de ce type), il serait pertinent de les regrouper dans un objet `platformCapabilities` ou de réévaluer `provide/inject`.
