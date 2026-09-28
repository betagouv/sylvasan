# 9. Catégories de vocabulaire pour le contrôle d'accès aux référentiels

Date: 2026-09-28

## Statut

Accepté

## Contexte

Les `VocabularySet` (référentiels) étaient jusqu'ici liés à une organisation via une clé étrangère `organisation`. Ce modèle supposait qu'un référentiel appartient à une organisation précise et n'est accessible qu'à ses membres.

Ce modèle devient insuffisant pour plusieurs raisons :

- Plusieurs organisations auront besoin d'accéder aux mêmes référentiels (ex. : les espèces forestières, les codes problèmes DSF). Dupliquer les données par organisation entraînerait une divergence progressive entre les copies et un coût de maintenance élevé.
- On vise à standardiser les référentiels autant que possible, de façon à ce que plusieurs organisations partagent un même vocabulaire commun plutôt que de maintenir des variantes parallèles.
- La clé étrangère `organisation` sur `VocabularySet` était sémantiquement ambiguë : elle désignait tantôt l'auteur du référentiel, tantôt l'organisation y ayant accès.

## Décision

On introduit un champ `category` (type `TextChoices`) sur `VocabularySet`, et un champ `vocabulary_categories` (type `ArrayField`) sur `Organisation`.

- Chaque `VocabularySet` appartient à une catégorie thématique (ex. : `"forest"`).
- Chaque `Organisation` déclare la liste des catégories auxquelles elle a accès.
- L'accès d'un utilisateur à un référentiel est déterminé par l'union des catégories de ses organisations.

La clé étrangère `organisation` est conservée sur `VocabularySet` avec le rôle d'auteur ou créateur du référentiel, sans influence sur les droits d'accès.

La contrainte `unique_together` passe de `("organisation", "code")` à `("category", "code")`.

## Alternatives considérées

### Modèle Django `VocabularyCategory` avec relation M2M

Une première approche consistait à créer un modèle `VocabularyCategory` (table dédiée) avec une relation Many-to-Many vers `Organisation`.

Avantages :
- Widget natif dans l'admin Django (`filter_horizontal`)
- Possibilité d'ajouter des attributs aux catégories (description, icône, etc.)

Inconvénients :
- Jointure supplémentaire à chaque requête d'accès
- Complexité accrue (modèle, migration, factory, admin)
- Les catégories changent rarement et sont toujours versionnées avec le code : une table dédiée apporte peu de valeur par rapport à une enum

### `TextChoices` + `ArrayField` PostgreSQL (solution retenue)

Les catégories sont définies comme `models.TextChoices` dans le code source, et chaque `Organisation` stocke sa liste de catégories dans un `ArrayField`.

Avantages :
- Aucune jointure : le filtre `category__in=accessible` est direct
- Modèle plus simple, moins de tables
- Les catégories sont versionnées avec le code, ce qui garantit la cohérence entre le comportement applicatif et les données

Inconvénients :
- Spécifique à PostgreSQL (`django.contrib.postgres`)
- L'ajout d'une nouvelle catégorie nécessite une modification du code (enum) et une migration pour peupler les nouvelles données
- Le widget admin pour `ArrayField` nécessite un `ModelForm` personnalisé (`MultipleChoiceField` + `CheckboxSelectMultiple`)

## Conséquences

### Positives

- Plusieurs organisations peuvent accéder aux mêmes référentiels sans duplication de données
- La logique d'accès est centralisée dans `_accessible_vocab_queryset`, facile à tester et à faire évoluer
- Les catégories sont explicites dans le code : tout changement de périmètre est traçable via git

### Négatives

- L'ajout d'une catégorie demande une modification du code en plus d'une migration de données

### Comportement des référentiels sans catégorie (`category = NULL`)

Un `VocabularySet` avec `category = NULL` est actuellement invisible de tous les utilisateurs. En SQL, `NULL IN ('forest', ...)` s'évalue toujours à `NULL` (jamais à `TRUE`), ce qui exclut ces référentiels de toute requête filtrée par catégorie.

Ce comportement est intentionnel : un référentiel sans catégorie est considéré comme non publié. À l'avenir, si le besoin se présente, une logique spécifique pourra être ajoutée pour traiter les référentiels à catégorie nulle différemment (ex. : visibles des administrateurs, ou à l'organisation créatrice).
