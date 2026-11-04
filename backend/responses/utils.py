import datetime
import math

from rest_framework.exceptions import ValidationError


def validate_bbox(params):
    """Valide et retourne (south, west, north, east) depuis les query params."""
    try:
        south = float(params["south"])
        west = float(params["west"])
        north = float(params["north"])
        east = float(params["east"])
    except (KeyError, ValueError):
        raise ValidationError(
            "Les paramètres south, west, north et east sont obligatoires et doivent être des nombres."
        )
    if not all(math.isfinite(v) for v in (south, west, north, east)):
        raise ValidationError("Les paramètres south, west, north et east doivent être des nombres finis.")
    if south >= north:
        raise ValidationError("south doit être strictement inférieur à north.")
    return south, west, north, east


def parse_ids(raw, param_name):
    """Convertit une chaîne d'identifiants séparés par des virgules en liste d'entiers."""
    try:
        return [int(s.strip()) for s in raw.split(",") if s.strip()]
    except ValueError:
        raise ValidationError(
            f"Le paramètre {param_name} doit contenir des identifiants numériques séparés par des virgules."
        )


def parse_date(raw, param_name):
    """Convertit une chaîne ISO en date."""
    try:
        return datetime.date.fromisoformat(raw)
    except ValueError:
        raise ValidationError(f"Le paramètre {param_name} doit être une date au format YYYY-MM-DD.")
