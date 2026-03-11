# Application mobile

Cette application Typescript utilise Capacitor et Ionic pour générer des applications natives sur Android et iOS.

## Environnements

Il faut trois fichiers `.env` :

- .env (utilisé lors des builds dev)
- .env.development
- .env.staging
- .env.production

## Android

Assurez-vous d'avoir l'[environnement nécessaire installé](https://capacitorjs.com/docs/getting-started/environment-setup#android-requirements).

### Tests en local

#### Créez une build
Pour créer une build : `npm run build-dev` `npm run build-staging` ou `npm run build-production` en dépendant de l'environnement souhaité

#### Copiez l'output
Pour passer la build à l'app Android : `npx cap sync android`

#### Lancez dans l'emulateur
Pour voir l'application et choisir le device : `npx cap run android`

#### Débug
Sur Chrome, allez dans `chrome://inspect/#devices` et choisissez le device en cours

### Release

#### Créez une build
Pour créer une build : `npm run build-staging` ou `npm run build-production` en dépendant de l'environnement souhaité

#### Copiez l'output
Pour passer la build à l'app Android : `npx cap sync android`

#### Ouvrez Android Studio
Pour passer la build à l'app Android : `npx cap open android`

#### Changez le numéro de version
Sur *mobile/android/app/build.gradle* modifiez le numéro de version

#### Créez l'AAB
Sur Android Studio allez dans *Build -> Generate Signed App Bundle or APK*

Séléctionnez *Android App Bundle*, variante *Release*.

#### Téléchargez l'AAB
Le résultat de la build se trouve dans *mobile/app/release/app-release.aab*
