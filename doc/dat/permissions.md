# Permissions

Nous avons actuellement deux rôles : Admin et Responder. Pour chacun de ces rôles, le scope peut être au niveau de toute l'organisation, ou au niveau d'un ou plusiers pôles.

Le rôle *Django super-admin* décrit ce qui est possible de faire via l'interface administration de Django.

Ce document vise à clarifier quels droits sont attribués à chaque rôle.

## Enquêtes

### Voir les enquêtes

Les enquêtes sont visibles par exemple via `/enquetes` dans le web.

|  | Voir les enquêtes au niveau organisation | Voir les enquêtes au niveau de son pôle | Voir les enquêtes au niveau d'un autre pôle |
|----------------|--------------------------------------------|-----------------------------------------|---------------------------------------------|
| Admin org      | ✅ | ✅ | ✅ |
| Admin pôle     | ❌ (Probabelement à changer) | ✅ | ❌ |
| Responder org  | ✅ | ✅ | ✅ |
| Responder pôle | ✅ | ✅ | ❌ |
|  |
| *Django super-admin* | ✅ | ✅ | ✅ |

### Créer des enquêtes

|  | Créer des enquêtes au niveau organisation | Créer des enquêtes au niveau de son pôle | Créer des enquêtes au niveau d'un autre pôle |
|----------------|--------------------------------------------|-----------------------------------------|---------------------------------------------|
| Admin org      | ✅ | ✅ | ✅ |
| Admin pôle     | ❌ | ✅ | ❌ |
| Responder org  | ❌ | ❌ | ❌ |
| Responder pôle | ❌ | ❌ | ❌ |
|  |
| *Django super-admin* | ✅ | ✅ | ✅ |

### Modifier des enquêtes

Modifier les enquêtes comprend l'ajout ou suppression des champs, modification de titres, etc.

|  | Modifier les enquêtes au niveau organisation | Modifier les enquêtes au niveau de son pôle | Modifier les enquêtes au niveau d'un autre pôle |
|----------------|--------------------------------------------|-----------------------------------------|---------------------------------------------|
| Admin org      | ✅ | ✅ | ✅ |
| Admin pôle     | ❌ | ✅ | ❌ |
| Responder org  | ❌ | ❌ | ❌ |
| Responder pôle | ❌ | ❌ | ❌ |
|  |
| *Django super-admin* | ✅ | ✅ | ✅ |

### Supprimer des enquêtes

À noter que les enquêtes supprimées restent en base de données mais ne sont plus prises en compte dans l'application.

|  | Supprimer les enquêtes au niveau organisation | Supprimer les enquêtes au niveau de son pôle | Supprimer les enquêtes au niveau d'un autre pôle |
|----------------|--------------------------------------------|-----------------------------------------|---------------------------------------------|
| Admin org      | ✅ | ✅ | ✅ |
| Admin pôle     | ❌ | ✅ | ❌ |
| Responder org  | ❌ | ❌ | ❌ |
| Responder pôle | ❌ | ❌ | ❌ |
|  |
| *Django super-admin* | ✅ | ✅ | ✅ |

## Réponses

### Voir les réponses

En ce moment les répondant·e·s peuvent seulement voir leurs propres réponses. Le tableau ci-dessous décrit ce qui devrait se passer prochainement.

|  | Voir les réponses au niveau organisation | Voir les réponses au niveau de son pôle | Voir les réponses au niveau d'un autre pôle |
|----------------|--------------------------------------------|-----------------------------------------|---------------------------------------------|
| Admin org      | ✅ | ✅ | ✅ |
| Admin pôle     | ❌ | ✅ | ❌ |
| Responder org  | ✅ | ✅ | ✅ |
| Responder pôle | ❌ | ✅ | ❌ |
|  |
| *Django super-admin* | ✅ | ✅ | ✅ |

### Créer des réponses

|  | Créer des réponses au niveau organisation | Créer des réponses au niveau de son pôle | Créer des réponses au niveau d'un autre pôle |
|----------------|--------------------------------------------|-----------------------------------------|---------------------------------------------|
| Admin org      | ❌ | ❌ | ❌ |
| Admin pôle     | ❌ | ❌ | ❌ |
| Responder org  | ✅ | ✅ | ✅ |
| Responder pôle | ✅ | ✅ | ❌ |
|  |
| *Django super-admin* | ✅ | ✅ | ✅ |

### Modifier des réponses

Lors que les réponses sont encore en brouillon dans le téléphone, elles peuvent être modifiées. Dans ce tableau on parle des réponses déjà envoyées.

|  | Modifier des réponses au niveau organisation | Modifier des réponses au niveau de son pôle | Modifier des réponses au niveau d'un autre pôle |
|----------------|--------------------------------------------|-----------------------------------------|---------------------------------------------|
| Admin org      | ❌ | ❌ | ❌ |
| Admin pôle     | ❌ | ❌ | ❌ |
| Responder org  | ❌ | ❌ | ❌ |
| Responder pôle | ❌ | ❌ | ❌ |
|  |
| *Django super-admin* | ✅ | ✅ | ✅ |

### Supprimer des réponses

À noter que les réponses supprimées restent en base de données mais ne sont plus prises en compte dans l'application.

|  | Modifier des réponses au niveau organisation | Modifier des réponses au niveau de son pôle | Modifier des réponses au niveau d'un autre pôle |
|----------------|--------------------------------------------|-----------------------------------------|---------------------------------------------|
| Admin org      | ✅ | ✅ | ✅ |
| Admin pôle     | ❌ | ✅ | ❌ |
| Responder org  | ❌ | ❌ | ❌ |
| Responder pôle | ❌ | ❌ | ❌ |
|  |
| *Django super-admin* | ✅ | ✅ | ✅ |
