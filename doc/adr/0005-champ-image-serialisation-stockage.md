# 5. Champ image — sérialisation, vignette, URL et stockage mobile

Date : 2026-05-28

## Statut

Accepté

## Contexte

L'application permet aux agents de terrain de joindre des photos à leurs réponses d'enquête. Ces photos sont prises sur mobile, potentiellement hors connexion, et doivent être transmises au backend lors de la soumission.

Plusieurs contraintes guident les décisions :

- **Volume** : une photo compressée côté mobile peut peser jusqu'à 2 Mo. Stocker plusieurs photos en base64 dans une réponse JSON alourdit significativement les échanges et le stockage local.
- **Offline-first** : les réponses peuvent être rédigées sans connexion et soumises plus tard. Le stockage local du mobile doit supporter ce cas sans saturer les mécanismes de persistance clé-valeur (`localStorage`, `NSUserDefaults`, `SharedPreferences`), qui ne sont pas conçus pour des données binaires volumineuses.
- **Affichage** : afficher les photos complètes dans des listes ou des résumés serait inutilement coûteux ; une vignette suffit. L'accès à la photo en pleine résolution doit toutefois rester possible depuis l'interface web.

## Décisions

### 1. Widget et type de champ

Le champ image est déclaré dans le schéma de l'enquête avec `type: "array"` (la valeur stockée est un tableau d'objets) et `ui.widget: "image"`. Un nouveau widget `"image"` a été ajouté à `FieldWidget` dans `shared/types/survey.d.ts` et au métaschéma JSON (`backend/surveys/metaschema.json`).

Le choix de `type: "array"` plutôt qu'un nouveau type primitif (`"file"`) est volontaire : `FieldType` reflète la forme JSON des données (un tableau d'objets), pas leur sémantique métier. Cela évite d'introduire un type non standard dans le métaschéma.

### 2. Sérialisation à la soumission : base64 inline

Le mobile envoie les images en base64 inline dans le corps de la requête, au format :

```json
{ "photo_arbre": [{ "file": "<base64>" }, { "file": "<base64>" }] }
```

À noter que côté frontend - mobile et web - le `ImagesField.vue` effectue une compression de l'image pour s'assurer qu'elle ne dépasse pas la taille limite imposée par le backend.

**Avantage principal** : la soumission est atomique — une seule requête, soit entièrement réussie, soit entièrement échouée. Il n'y a pas de gestion d'état partiel (ex. « photos uploadées, réponse échouée »).

**Limite acceptée** : les images transitent en base64, ce qui représente environ 33 % de surcharge par rapport au binaire. Cette surcharge est acceptable pour des photos compressées ≤ 2 Mo par image (limite validée côté sérialiseur Django).

### 3. Stockage backend : modèle `ResponseImage`

Côté backend, chaque image est extraite du champ `data` JSON lors de la création de la réponse et stockée dans un modèle dédié `ResponseImage` (fichier original + vignette). Le champ `data` de la réponse est ensuite mis à jour pour remplacer les données base64 par des références légères.

Le traitement se fait dans `ResponseSerializer._create_images_from_data()`, dans une transaction atomique. En cas d'échec, toute la réponse est annulée.

### 4. Vignette base64 en réponse

Après création, le sérialiseur retourne une vignette en base64 (200×200 px, JPEG qualité 60) plutôt que l'image complète :

```json
{ "photo_arbre": [{ "id": 1, "thumbnail": "<base64_vignette>", "fileUrl": "https://..." }] }
```

La vignette est générée par Pillow au moment de l'enregistrement et stockée sur disque/S3 séparément du fichier original. Elle est encodée en base64 dans la réponse API afin d'être stockable directement dans les `Preferences` Capacitor du mobile (quelques Ko au lieu de plusieurs Mo).

### 5. URL du fichier complet (`fileUrl`)

En plus de la vignette, le sérialiseur retourne une URL vers le fichier complet (`fileUrl`). Cette URL permet à l'interface web d'afficher la photo en pleine résolution dans la visionneuse plein écran, sans avoir à retransmettre des données volumineuses.

Le champ `file_url` (converti en `fileUrl` par `CamelCaseJSONRenderer`) est calculé dans `ResponseImageSerializer.get_file_url()` :

- En production (S3/Cellar) : `obj.file.url` retourne déjà une URL absolue publique (`AWS_QUERYSTRING_AUTH = False`).
- En développement local : le chemin relatif (`/media/...`) est préfixé avec `settings.HOSTNAME`.

Les URL S3 sont publiques mais non devinables (nom de fichier basé sur un UUID). Cette approche est commune dans les applications web et est jugée acceptable pour ce contexte.

### 6. Stockage mobile offline : `@capacitor/filesystem`

Lors de la sauvegarde d'un brouillon, les images en base64 présentes dans le formulaire sont écrites sur le système de fichiers natif via `@capacitor/filesystem` (`Directory.Data`), et remplacées dans les données du brouillon par des références légères :

```typescript
// Stocké dans Preferences (léger)
{ "photo_arbre": [{ "type": "local", "path": "response_images/<uuid>.jpg" }] }
```

**Raison** : les mécanismes de persistance clé-valeur (`@capacitor/preferences` → `localStorage` sur navigateur, `NSUserDefaults` sur iOS, `SharedPreferences` sur Android) ont des limites de taille qui rendent le stockage de données binaires volumineuses non viable.

La conversion est gérée dans `mobile/src/utils/imageStorage.ts` :

- `saveImagesToFilesystem(data, schema)` : écrit les images base64 sur disque, retourne les données avec les chemins.
- `loadImagesFromFilesystem(data)` : relit les fichiers depuis le disque et retourne les données avec les base64 (utilisé juste avant la soumission API).
- `deleteLocalImages(data)` : supprime les fichiers locaux (appelé après soumission réussie ou suppression du brouillon).

La suppression des fichiers locaux est couplée à la suppression du brouillon (`responses.ts:deleteDraft`) et à la soumission réussie (`responses.ts:submitResponse`) pour éviter les fichiers orphelins.

### 7. Affichage des images locales

Avant soumission, les `FilesystemImageItem` sont affichés dans l'interface via `Capacitor.convertFileSrc(path)`, qui traduit un chemin natif en URL accessible par la WebView. Cette conversion n'est jamais appelée dans l'application web (les `FilesystemImageItem` n'y apparaissent jamais).

## Types partagés

Trois types sont exportés depuis `shared/types/survey.d.ts` pour représenter les états successifs d'un élément image :

```typescript
type LocalImageItem       = { file: string } // Base64 en mémoire (formulaire web)
type FilesystemImageItem  = { type: "local"; path: string } // Fichier local (brouillon mobile)
type RemoteImageItem      = { id: number; thumbnail: string | null; fileUrl?: string } // Stocké backend
type ImageItem = LocalImageItem | FilesystemImageItem | RemoteImageItem
```

## Alternatives considérées

### Upload d'images en deux temps (multipart séparé)

Uploader les photos dans une première requête, puis soumettre la réponse avec des identifiants dans une seconde.

Rejeté : crée un état partiel difficile à gérer (images uploadées mais réponse échouée ou non soumise), incompatible avec l'approche offline-first et la garantie d'atomicité.

### Stockage des images dans IndexedDB (mobile)

IndexedDB supporte les données binaires sans limite de taille rigide et est disponible dans les WebViews.

Rejeté : `@capacitor/filesystem` est déjà utilisé pour le stockage des tuiles cartographiques hors ligne — réutiliser la même API maintient la cohérence du code. IndexedDB nécessiterait une dépendance supplémentaire (ex. `idb`) ou une gestion manuelle plus complexe.

### Pas de vignette — URL uniquement

Retourner uniquement une URL vers l'image complète, sans vignette base64.

Rejeté : charger des images complètes pour afficher des miniatures dans une grille serait coûteux en bande passante, particulièrement sur mobile avec une connexion limitée. La vignette stockée localement permet un affichage immédiat même hors connexion partielle.

## Conséquences

### Positives

- Soumission atomique : pas d'état partiel à gérer.
- Brouillons légers : les `Preferences` ne contiennent que des chemins de fichiers.
- Affichage rapide des vignettes dans les listes et résumés.
- Accès à la pleine résolution depuis le web via `fileUrl`.

### Négatives

- Complexité du cycle de vie des fichiers locaux : il faut s'assurer que `deleteLocalImages` est appelé dans tous les chemins de suppression (soumission réussie, suppression manuelle du brouillon).
- Les réponses stockées avant l'introduction de ce champ ne contiennent pas de `fileUrl` — le code doit gérer cette absence gracieusement (`fileUrl` est optionnel dans `RemoteImageItem`).
- En développement navigateur, les images restent en base64 en mémoire et saturent `localStorage` si l'on teste avec de nombreuses photos. Ce comportement est accepté comme limitation connue de l'environnement de développement.
