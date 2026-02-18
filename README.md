# SylvaSan

Faciliter le relevé et le suivi des problèmes sanitaires des arbres en forêt

## Installation du projet

#### À installer localement

- [Python3](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installing/)
- [Node et npm](https://nodejs.org/en/download/)
- [Postgres](https://www.postgresql.org/download/)

#### Création d'un environnement Python3

C'est recommandé de créer un environnement virtuel avec Python3.

```
python -m venv venv
source ./venv/bin/activate
```

#### Installer les dépendances du backend

Les dépendances du backend se trouvent dans `/backend/requirements.txt`. Pour les installer :

```
pip install -r requirements.txt
```

#### Installer les dépendances de l'application web

L'application web se trouve sous `/web`. Pour installer les dépendances :

```
cd frontend
npm ci
```

#### Installer les dépendances de l'application mobile

L'application mobile se trouve sous `/mobile`. Pour installer les dépendances :

```
cd frontend
npm ci
```

#### Créer la base de données

Par exemple, pour utiliser une base de données nommée _sylvasan_ :

```
createdb sylvasan
```
Le user doit avoir les droits de creation

```
sudo su postgres
postgres=# create user <DB_USER> createdb password <DB_PASSWORD>;
```

#### Pre-commit

Nous utilisons [`pre-commit`](https://pre-commit.com/) pour effectuer des vérifications automatiques
avant chaque commit. Cela permet par exemple de linter les code Python, Javascript et HTML.

Pour pouvoir l'utiliser, assurez-vous d'être dans votre environnement virtuel, et activez-le avec `pre-commit install`.

Les vérifications seront ensuite effectuées avant chaque commit. Attention, lorsqu'une vérification `fail`,
le commit est annulé. Il faut donc que toutes les vérifications passent pour que le commit soit pris en
compte. Si exceptionnellement vous voulez commiter malgré qu'une vérification ne passe pas, c'est possible
avec `git commit -m 'my message' --no-verify`.

#### Compléter les variables d'environnement

L'application utilise [django-environ](https://django-environ.readthedocs.io/en/latest/), vous pouvez donc créer un fichier `.env` à la racine du projet avec ces variables définies :

```
SECRET= Le secret pour Django (vous pouvez le [générer ici](https://djecrety.ir/))
DEBUG= `True` pour le développement local ou `False` autrement
DB_USER= L'utilisateur de la base de données. Doit avoir les droits de creation de db pour les tests.
DB_PASSWORD= Le mot de passe pour accéder à la base de données
DB_HOST= Le host de la base de données (par ex. '127.0.0.1')
DB_PORT= Le port de la base de données (par ex. '3306')
DB_NAME= Le nom de la base de données (par ex. 'sylvasan')
HOSTNAME= Le hostname dans lequel l'application se trouve (par ex. 127.0.0.1:8000)
ALLOWED_HOSTS= Des noms de domaine/d’hôte que ce site peut servir (par ex. 'localhost, \*')
STATICFILES_STORAGE= Le système utilisé pour les fichiers statiques (par ex. 'django.contrib.staticfiles.storage.StaticFilesStorage')
DEFAULT_FILE_STORAGE= Le système de stockage de fichiers (par ex 'django.core.files.storage.FileSystemStorage')
FORCE_HTTPS= 'False' si on développe en local, 'True' autrement
SECURE= 'False' si on développe en local, 'True' autrement
ENVIRONMENT= Optionnel - si cette variable est remplie un badge sera visible dans l'application et l'admin changera. Les options sont : `dev` | `staging` | `demo` | `prod`
DEFAULT_FROM_EMAIL= par ex. 'from@example.com'
CONTACT_EMAIL= par ex. 'contact@example.com'
EMAIL_BACKEND= par ex. 'django.core.mail.backends.console.EmailBackend'. Pour utiliser SendInBlue : 'anymail.backends.sendinblue.EmailBackend'
DEV_FRONTEND_ORIGINS= Une liste de hosts pour le développement en local. Cette liste doit contenir les applications web et mobile, normalement `localhost:5173,localhost:5174`
```

#### Créer les différents modèles Django dans la base de données

```
python manage.py migrate
```

## Lancement de l'application en mode développement

Pour le développement il faudra avoir trois terminales ouvertes :
- Une pour Django, sous /backend
- Une pour l'application web, sous /web
- Une pour l'application mobile, sous /mobile

### Terminal Django

Il suffit de lancer la commande Django "runserver" à la racine du projet pour avoir le serveur de développement (avec hot-reload) :

```
python manage.py runserver
```

### Terminal web et mobile

Pour faire l'équivalent côté web et mobile, allez sur leur racine et lancez le serveur npm :

```
cd web/mobile
npm run dev
```
