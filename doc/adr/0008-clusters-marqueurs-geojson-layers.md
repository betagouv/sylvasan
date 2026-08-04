# 8. Passage des marqueurs DOM aux couches GeoJSON pour l'affichage des pins et le clustering

Date : 2026-08-04

## Statut

Accepté

## Contexte

L'application mobile affiche sur une carte les réponses géolocalisées récupérées depuis le serveur (`useGeoPins.ts`). La première implémentation utilisait des `maplibregl.Marker`, çad des éléments DOM ajoutés au-dessus du canvas MapLibre. Ce choix était le plus simple pour les besoins du début, surtout que le nombre de pins restait faible, et nous permet d'avoit accès direct aux éléments HTML (style CSS, listeners d'événements).

La demande d'ajout du clustering a rendu ce choix intenable. De plus, on affiche maintenant sur l'écran les observations des collègues, non seulement celles de l'utilisateur·ice. Le clustering natif de MapLibre (`cluster: true` sur une source GeoJSON) fonctionne uniquement au niveau du moteur de rendu WebGL et est incompatible avec les marqueurs DOM, qui sont gérés indépendamment par le navigateur et invisibles de MapLibre.

## Décision

Le rendu des pins dans `useGeoPins.ts` migre entièrement vers une source GeoJSON avec trois couches MapLibre :

- `geo-pins-clusters` (type `circle`) : bulle de cluster.
- `geo-pins-cluster-count` (type `symbol`) : label numérique blanc centré sur la bulle.
- `geo-pins-unclustered` (type `symbol`) : icône en forme de pin (SVG encodé en image MapLibre via `addImage`), colorée selon que la réponse appartient à l'utilisateur connecté ou à un collègue.

Les constantes `CLUSTER_MAX_ZOOM` et `CLUSTER_RADIUS` sont exposées en tête de fichier pour faciliter le réglage.

Les données de chaque pin sont sérialisées en propriétés GeoJSON (les objets imbriqués comme `respondant` sont `JSON.stringify`és) et désérialisées à la sélection pour reconstruire le `PinData` complet.

## Comparaison des deux approches

### Marqueurs DOM (`maplibregl.Marker`)

**Avantages :**
- Stylisables directement en CSS ou avec des composants Vue.
- Chaque marqueur dispose de son propre listener d'événement. Pas besoin de délégation.
- Fonctionnent avant le chargement du style MapLibre (pas de `once("load")`).

**Inconvénients :**
- Incompatibles avec le clustering natif MapLibre.
- Les performances se dégradent à partir de quelques centaines d'éléments (le navigateur gère autant de nœuds DOM que de marqueurs).
- Le positionnement suit le thread principal : lors d'animations ou de déplacements rapides de la carte, les marqueurs peuvent se décaler du canvas.

### Couches GeoJSON

**Avantages :**
- Rendues dans le pipeline WebGL : des milliers de points sans surcharge DOM.
- Clustering natif disponible sans logique supplémentaire.
- Le style par donnée (couleur selon propriété) s'exprime avec des expressions MapLibre, sans itérer sur des éléments DOM.

**Inconvénients :**
- Les icônes personnalisées doivent être encodées en image MapLibre (`addImage`). Le CSS est inutilisable.
- Les listeners de clic passent par `map.on("click", layerId)` et `queryRenderedFeatures`, plus verbeux que `element.addEventListener`.
- Les propriétés GeoJSON sont plates et typées JSON : les objets complexes doivent être sérialisés/désérialisés manuellement.

## Alternatives considérées

### Approche hybride : marqueurs DOM pour les pins individuels, couche GeoJSON pour les clusters seulement

Gérer les clusters via une source GeoJSON et afficher les pins non-clusterisés comme des marqueurs DOM synchronisés à partir des features de la source.

Rejeté : la synchronisation entre la source GeoJSON et les marqueurs DOM est complexe. Il faut interroger les features rendues après chaque mouvement de carte pour savoir quels marqueurs afficher ou masquer, et gérer leur cycle de vie manuellement. La maintenance serait significativement plus lourde pour un gain marginal (les icônes pin sont reproduites fidèlement via `addImage`).

### Bibliothèque de clustering tierce (ex. supercluster)

Calculer les clusters côté JavaScript et les afficher comme des marqueurs DOM.

Rejeté : introduit une dépendance externe pour reproduire une fonctionnalité déjà intégrée à MapLibre. Conserve aussi les inconvénients des marqueurs DOM à grande échelle.

## Conséquences

### Positives

- Le clustering est géré nativement par MapLibre, sans logique applicative supplémentaire.
- L'implémentation supporte sans modification un volume de pins bien supérieur à l'ancienne approche DOM.
- Les pins individuels conservent l'apparence visuelle historique (icône en larme) grâce au SVG encodé.

### Négatives

- L'initialisation des couches doit attendre l'événement `load` de MapLibre, ce qui introduit un décalage minimal au premier affichage.
- Toute évolution de l'apparence des pins (animation, badge dynamique) nécessite de passer par l'API image MapLibre ou d'accepter les limitations des expressions de style.
- Les données du pin doivent être sérialisées en propriétés GeoJSON plates, ce qui implique un `JSON.stringify`/`JSON.parse` pour le champ `respondant`.
