"""
Synchronise les VocabularySet/VocabularyEntry DSF depuis l'API REST IGN/DSF.

Conçu pour être appelé depuis une commande de gestion ou une tâche Celery :

    from organisation_specific.dsf.sync_vocabularies_api import sync_dsf_vocabularies_from_api
    result = sync_dsf_vocabularies_from_api(dry_run=False, only_unite=None)
"""

import logging
import time

import requests
from organisations.models import Organisation
from surveys.models import VocabularyEntry, VocabularySet

logger = logging.getLogger(__name__)

DSF_API_BASE = "https://qlf-dsf.ign.fr/api"

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

# Unités blacklistées (obsolètes ou hors périmètre Sylvasan)
BLACKLISTED_UNITES = {
    "CMM",
    "CM2013",
    "CM",
    "CM2016",
    "CM2019",
    "QD8",
    "CODESP",
    "CT",
    "QD",
    "PB",
    "PBV2025",
    "PBPA2024",
    "PBV2024",
    "PBV2023",
    "PBPA2023",
    "PBPA2022",
    "PBV2022",
    "PBPA2021",
    "PBV2021",
    "PBPA2020",
    "PBV2020",
    "PB123",
    "PBPA2019",
    "PBV2019",
    "PBPA2018",
    "PBV2018",
}


class DSFApiError(Exception):
    """Levée quand l'API DSF est inaccessible ou renvoie des données inattendues après tous les essais."""


def _fetch_json(url: str, params: dict | None = None) -> tuple[list | dict, int]:
    """
    Récupère le JSON depuis *url*, en réessayant jusqu'à MAX_RETRIES fois en cas de réponse
    non-200 ou non-JSON. Retourne (json_parsé, taille_en_octets).
    Lève DSFApiError une fois tous les essais épuisés.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug("GET %s (attempt %d/%d)", url, attempt, MAX_RETRIES)
            response = requests.get(url, params=params, timeout=60)
        except requests.RequestException as exc:
            logger.warning("Attempt %d/%d — network error: %s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            raise DSFApiError(f"Network error after {MAX_RETRIES} attempts: {exc}") from exc

        content_length = len(response.content)

        if response.status_code != 200:
            logger.warning(
                "Attempt %d/%d — HTTP %d from %s",
                attempt,
                MAX_RETRIES,
                response.status_code,
                url,
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            raise DSFApiError(f"HTTP {response.status_code} after {MAX_RETRIES} attempts from {url}")

        try:
            data = response.json()
        except ValueError as exc:
            logger.warning(
                "Attempt %d/%d — non-JSON response from %s (content-type: %s)",
                attempt,
                MAX_RETRIES,
                url,
                response.headers.get("content-type", "?"),
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            raise DSFApiError(f"Non-JSON response after {MAX_RETRIES} attempts from {url}") from exc

        return data, content_length

    raise DSFApiError(f"Failed to fetch {url} after {MAX_RETRIES} attempts")


def sync_dsf_vocabularies_from_api(
    dry_run: bool = False,
    only_unite: str | None = None,
) -> dict:
    """
    Synchronise les référentiels DSF depuis l'API REST IGN/DSF vers VocabularySet/VocabularyEntry.

    Retourne un dictionnaire récapitulatif :
        {
            "sets_created": int,
            "sets_updated": int,
            "entries_created": int,
            "entries_updated": int,
            "entries_deactivated": int,
        }

    Lève DSFApiError si l'API est inaccessible après tous les essais (aucune modification en base).
    Lève Organisation.DoesNotExist si l'organisation DSF est absente.
    """
    logger.info("=== Début de la synchronisation DSF via API ===")
    if dry_run:
        logger.info("[dry-run] Aucune modification ne sera appliquée")

    dsf_org = Organisation.objects.get(name="DSF")

    # ------------------------------------------------------------------ #
    # 1. Récupérer toutes les unités, filtrer sur NOMINAL et blacklist    #
    # ------------------------------------------------------------------ #
    logger.info("Récupération des unités depuis %s/unites …", DSF_API_BASE)
    unites_data, unites_bytes = _fetch_json(f"{DSF_API_BASE}/unites")

    if not isinstance(unites_data, list):
        raise DSFApiError(f"Unexpected shape for /unites: {type(unites_data)}")

    logger.info(
        "Réponse /unites : %d unités, %.1f Ko",
        len(unites_data),
        unites_bytes / 1024,
    )

    all_types = [u.get("type") for u in unites_data]
    nominal_count_raw = sum(1 for t in all_types if t == "NOMINAL")

    nominal_unites: dict[str, dict] = {}
    for u in unites_data:
        code = u.get("unite", "")
        if u.get("type") != "NOMINAL":
            continue
        if code in BLACKLISTED_UNITES:
            logger.debug("Unité %s ignorée (blacklist)", code)
            continue
        nominal_unites[code] = u

    logger.info(
        "Unités API : %d au total, %d NOMINAL, %d après blacklist, %d en base de données (DSF)",
        len(unites_data),
        nominal_count_raw,
        len(nominal_unites),
        VocabularySet.objects.filter(organisation=dsf_org).count(),
    )

    if only_unite:
        if only_unite not in nominal_unites:
            logger.warning(
                "Unité '%s' introuvable parmi les unités NOMINAL de l'API (ou blacklistée)",
                only_unite,
            )
            return {
                "sets_created": 0,
                "sets_updated": 0,
                "sets_deactivated": 0,
                "entries_created": 0,
                "entries_updated": 0,
                "entries_deactivated": 0,
            }
        nominal_unites = {only_unite: nominal_unites[only_unite]}

    logger.info("%d unité(s) NOMINAL à synchroniser", len(nominal_unites))

    # ------------------------------------------------------------------ #
    # 2. Récupérer tous les modes en un seul appel                        #
    # ------------------------------------------------------------------ #
    modes_count_data, _ = _fetch_json(f"{DSF_API_BASE}/modes/count")
    total_modes = modes_count_data.get("count", 0)
    logger.info("Total modes dans l'API : %d", total_modes)

    limit = total_modes + 100  # marge de sécurité
    logger.info("Récupération de tous les modes (%d) depuis %s/modes …", total_modes, DSF_API_BASE)
    modes_data, modes_bytes = _fetch_json(f"{DSF_API_BASE}/modes", params={"limit": limit, "lang": "FR"})

    if not isinstance(modes_data, list):
        raise DSFApiError(f"Unexpected shape for /modes: {type(modes_data)}")

    logger.info(
        "Réponse /modes : %d modes reçus, %.1f Mo",
        len(modes_data),
        modes_bytes / (1024 * 1024),
    )

    # Regroupement des modes par unité, en ne conservant que les unités NOMINAL non blacklistées
    modes_by_unite: dict[str, list[dict]] = {code: [] for code in nominal_unites}
    for m in modes_data:
        unite_code = m.get("unite", "")
        if unite_code in modes_by_unite:
            modes_by_unite[unite_code].append(m)

    # ------------------------------------------------------------------ #
    # 3. Upsert des VocabularySet + VocabularyEntry                       #
    # ------------------------------------------------------------------ #
    totals = {
        "sets_created": 0,
        "sets_updated": 0,
        "sets_deactivated": 0,
        "entries_created": 0,
        "entries_updated": 0,
        "entries_deactivated": 0,
    }

    for unite_code, unite_info in nominal_unites.items():
        modes = modes_by_unite.get(unite_code, [])
        name = unite_info.get("libelle") or unite_code

        if not modes:
            logger.warning("Aucun mode trouvé pour l'unité '%s' — ignorée", unite_code)
            continue

        logger.debug("Unité '%s' (%s) : %d modes", unite_code, name, len(modes))

        if dry_run:
            for m in modes:
                logger.debug("  [dry-run] %s — %s (position: %s)", m.get("mode"), m.get("libelle"), m.get("position"))
            continue

        vocab, created = VocabularySet.objects.update_or_create(
            organisation=dsf_org,
            code=unite_code,
            defaults={"name": name, "is_active": True},
        )
        if created:
            totals["sets_created"] += 1
            logger.debug("VocabularySet '%s' créé", unite_code)
        else:
            totals["sets_updated"] += 1

        existing_codes = set(vocab.entries.values_list("code", flat=True))
        source_codes = {m["mode"] for m in modes}

        for m in modes:
            _, entry_created = VocabularyEntry.objects.update_or_create(
                vocabulary_set=vocab,
                code=m["mode"],
                defaults={
                    "label": m.get("libelle") or m.get("definition") or m["mode"],
                    "position": m.get("position"),
                    "is_active": True,
                },
            )
            if entry_created:
                totals["entries_created"] += 1
            else:
                totals["entries_updated"] += 1

        removed_codes = existing_codes - source_codes
        if removed_codes:
            deactivated = VocabularyEntry.objects.filter(
                vocabulary_set=vocab,
                code__in=removed_codes,
                is_active=True,
            ).update(is_active=False)
            totals["entries_deactivated"] += deactivated
            if deactivated:
                logger.warning(
                    "Unité '%s' : %d entrée(s) désactivée(s) : %s",
                    unite_code,
                    deactivated,
                    ", ".join(sorted(removed_codes)),
                )

    # Désactivation des VocabularySets DSF absents de l'API (synchronisation complète uniquement)
    if not only_unite and not dry_run:
        sets_deactivated = (
            VocabularySet.objects.filter(
                organisation=dsf_org,
                is_active=True,
            )
            .exclude(code__in=nominal_unites)
            .update(is_active=False)
        )
        totals["sets_deactivated"] = sets_deactivated
        if sets_deactivated:
            logger.warning("%d VocabularySet(s) désactivé(s) (absents de l'API)", sets_deactivated)

    logger.info(
        "=== Synchronisation terminée : %d sets créés, %d mis à jour, %d désactivés, "
        "%d entrées créées, %d mises à jour, %d désactivées ===",
        totals["sets_created"],
        totals["sets_updated"],
        totals["sets_deactivated"],
        totals["entries_created"],
        totals["entries_updated"],
        totals["entries_deactivated"],
    )
    return totals
