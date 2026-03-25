# 2. Architecture multi-organisation avec extensions spécifiques

Date: 2026-03-25

## Statut

Accepté

## Contexte

Le projet vise dans un premier temps à remplacer EpiCollect pour le DSF. Cependant, l'outil de saisie de formulaires terrain a vocation à être réutilisé par d'autres organisations ayant des besoins similaires.

Le DSF dispose d'un écosystème technique existant avec lequel l'application doit s'intégrer :
- Une base de vocabulaire contrôlé (`metadsf` aka metadonnées) référençant les espèces, symptômes, codes problèmes, etc.
- Des schémas de base de données existants (`dsffs`, `gener`) vers lesquels les réponses doivent être exportées
- Un système d'authentification propre (`dsfp`) gérant les comptes et droits des agents que nous pouvons éventuellement utiliser

Ces spécificités sont propres au DSF et ne doivent pas contraindre l'utilisation de la plateforme par d'autres organisations. De plus, les éventuelles futures organisations utilisatrices de SylvaSan peuvent elles-aussi avoir des données existantes.

## Décision

L'application est structurée en deux couches distinctes :

Une plateforme générique (applications Django `organisations`, `surveys`, `responses`) qui expose les fonctionnalités de base : création de formulaires simples, saisie de réponses, gestion des organisations et des pôles, vocabulaire contrôlé.

Des extensions par organisation regroupées dans le dossier `organisation_specific/<nom_org>/`, chacune étant une application Django autonome pouvant apporter :
- Un backend d'authentification propre
- Des types d'enquêtes personnalisés avec comportements métier spécifiques
- Des exporteurs vers les schémas cibles de l'organisation
- Des tâches Celery de synchronisation (par ex. : import du vocabulaire `metadsf`)

Les types d'enquêtes (`SurveyType`) sont définis comme enum dans le code, et non en base de données, afin d'éviter tout désynchronisation entre le comportement attendu et les données enregistrées. L'ajout d'un nouveau type dans cet enum nécessite aussi le code spécifique qui gére la logique.

## Alternatives considérées

### Tout coder pour le DSF uniquement

Avantages :
- Développement initial plus rapide
- Moins d'abstraction à concevoir

Inconvénients :
- Outil inexploitable tel quel par une autre organisation
- Refactorisation coûteuse si une réutilisation est envisagée ultérieurement
- Les spécificités DSF (authentification, exports, vocabulaire) seraient mélangées au code métier générique

### Plateforme entièrement générique, sans extensions

Avantages :
- Code uniforme, plus simple à maintenir

Inconvénients :
- Impossibilité d'intégrer les workflows existants du DSF sans modifier le cœur
- Reproduit les mêmes points de douleur qu'EpiCollect : double saisie du vocabulaire, exports manuels, absence de lien avec les schémas existants

## Conséquences

### Positives
- Une organisation simple (sans base de données existante) peut utiliser la plateforme sans configuration particulière
- Les spécificités du DSF sont isolées et versionnées avec le reste du code
- L'ajout d'une nouvelle organisation se fait sans modifier le cœur de la plateforme
- La séparation des responsabilités facilite les tests et la maintenance
- Le vocabulaire contrôlé du DSF (`metadsf`) peut être importé automatiquement, éliminant la double saisie manuelle actuelle

### Négatives
- La conception initiale demande davantage de réflexion qu'une approche DSF-only
- Les devs d'une nouvelle organisation doivent comprendre le contrat d'interface des extensions avant de pouvoir contribuer
- Certains comportements dynamiques (authentification selon l'organisation de l'utilisateur) nécessitent une attention particulière à la configuration des backends Django
