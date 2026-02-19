# 1. Choix de Vue + Capacitor pour l'application mobile

Date: 2026-02-11

## Statut

Accepté

## Contexte

Le projet comprendra une application mobile (Android et iOS) et une application web. Les deux offriront des fonctionnelles similaires et donc peuvent partanger des briques communes.

Ces applications ont un besoin d’intégration avec une API Django REST. Il faut noter également que l'équipe actuel est déjà familiarisé avec Vue.js

Plusieurs technologies étaient envisageables : React Native, Flutter, développement natif ou Ionic.

## Décision

L’application mobile sera développée avec Vue 3, Ionic et Capacitor.

La base de code pourra être partagée avec la version web lorsque cela est pertinent (logique métier, schémas, types, couche API).

Concernant la gestion del cartes IGN offline, nous pourrons nous appuyer sur le code existant de l'application mobile de l'IGN, elle aussi basée sur Javascript.

### Alternatives considérées

#### React Native

Avantages :
- Performances proches du natif
- Large communauté

Inconvénients :
- Montée en compétence de React
- Complexité accrue pour le partage de vues entre React web et React native

#### Flutter

Avantages :
- Excellentes performances
- UI homogène

Inconvénients :
- Conformité DSFR
- A11y
- Langage Dart
- Aucun partage direct de code avec le web

#### Développement natif (Swift / Kotlin)

Avantages :
- Performances maximales
- Intégration OS complète

Inconvénients :
- Double développement
- Coût de maintenance élevé
- Faible mutualisation
- Conformité DSFR


## Conséquences

### Positives
- Mutualisation du code possible avec la version web
- Stack technologique cohérente (Vue partout)
- Réduction des coûts de maintenance
- Time-to-market plus rapide
- Simplicité de recrutement

### Négatives
- Performance légèrement inférieure au natif
- Dépendance à Ionic et Capacitor
- Certaines intégrations natives nécessiteront des plugins
