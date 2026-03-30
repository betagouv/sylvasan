# 3. Partage de types entre applications TS

Date : 2026-03-30

## Statut

Accepté

## Contexte

Le monorepo du projet contient deux applications basées sur Vue / Typescript :

- /web : application web Vue (TS)
- /mobile : application mobile Vue (TS) + Capacitor

Ces deux applications peuvent utilisent les mêmes structures de données, et donc interfaces TypeScript, issues de l’API Django. Le partage des définitions de types (par exemple, des réponses d’enquête, des formulaires, etc.) est essentiel.

À terme, d’autres contenus pourraient également être mutualisés (composants Vue, utilitaires, logique métier). Toutefois, dans un premier temps, seul le besoin de partager les types est présent.

La stack technique actuelle utilise Vite pour le build, et un servur de fichiers statiques Apache pour servir l’application web (après un npm run build).

## Décision

Nous avons opté pour une solution légère basée sur les alias de chemin TypeScript et Vite. Un dossier shared/types a été créé à la racine du projet contenant les définitions de types communes.

Dans chaque application frontend :

- Le tsconfig.app.json inclut une configuration paths pour résoudre @shared-types/* vers le dossier partagé.
- Le vite.config.ts déclare un alias @shared-types correspondant.

Cette approche permet d’importer les types de cette façon :

```typescript
import type { BoundaryBox, OfflineMapRecord } from '@shared-types';
```

Les déclarations globales (ex. `window.ENVIRONMENT`) sont placées dans un fichier .d.ts dans le dossier partagé, et ce dossier est ajouté à la section include du tsconfig.app.json pour que TypeScript les prenne en compte.

## Alternatives considérées

### Option 1 – Paquet partagé dans l’espace de travail (workspace package)

Cette solution consisterait à créer un paquet shared-types dans packages/, géré via les workspaces npm/yarn/pnpm, et à l’ajouter comme dépendance locale des applications.

Raisons du rejet temporaire :

- Nécessite de configurer un package.json à la racine du monorepo, avec la gestion des workspaces.
- Impacte la configuration de Dependabot (il faudrait l’adapter pour le nouveau paquet).
- Le serveur Apache actuel est paramétré pour builder indépendamment web et mobile ; l’introduction d’un paquet partagé nécessiterait des modifications de la CI.
- Le volume actuel de types partagés ne justifie pas encore l’investissement.

### Option 2 – Références de projet TypeScript (project references)

TypeScript permet de référencer un autre projet via les references dans le tsconfig.

Raisons du rejet :
- Complexité de configuration avec Vite (les références nécessitent souvent une étape de compilation intermédiaire).
- Moins répandu dans l’écosystème Vite.

## Conséquences

### Positives

- Mise en œuvre rapide : quelques lignes de configuration par application.
- Aucune modification du build existant ni de la configuration Dependabot
- Évolutif : si le besoin de partager du code plus complexe (composants, utilitaires) se confirme, nous pourrons migrer facilement vers une autre option.
- Pas de surcharge de versionnage : les types restent synchronisés avec le code des applications.

### Négatives

- Pas de versionnage explicite : toutes les applications utilisent la même version des types.
- Risque de chemins relatifs fragiles : la configuration repose sur des chemins relatifs (../shared/types) ; un déplacement ou une réorganisation pourrait casser les imports.
- Déclarations globales nécessitent un include explicite : les fichiers .d.ts doivent être ajoutés à include dans chaque tsconfig.app.json, ce qui peut être oublié lors de l’ajout de nouvelles déclarations.

## Évolution future

Si le volume de code partagé augmente (composants Vue, logique métier, etc.), nous réévaluerons l’option du paquet partagé (Option 1).
