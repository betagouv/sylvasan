from django.db.models import Count
from django.db.models.functions import TruncMonth

from responses.models import Response as SurveyResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from surveys.models import Survey
from users.models import User

_MONTHS_FR = {
    1: "Jan.",
    2: "Fév.",
    3: "Mars",
    4: "Avr.",
    5: "Mai",
    6: "Juin",
    7: "Juil.",
    8: "Août",
    9: "Sep.",
    10: "Oct.",
    11: "Nov.",
    12: "Déc.",
}


def _cumulative_monthly(queryset, date_field="creation_date"):
    rows = (
        queryset.annotate(month=TruncMonth(date_field)).values("month").annotate(count=Count("id")).order_by("month")
    )
    labels = []
    data = []
    total = 0
    for row in rows:
        m = row["month"]
        labels.append(f"{_MONTHS_FR[m.month]} {m.year}")
        total += row["count"]
        data.append(total)
    return labels, data


class StatsAPIView(APIView):
    def get(self, request):
        stats = []

        labels, data = _cumulative_monthly(User.objects.filter(is_active=True))
        stats.append(
            {
                "id": "active-users",
                "type": "line",
                "title": "Comptes actifs",
                "description": "Nombre cumulatif de comptes actifs, par mois de création.",
                "data": {
                    "labels": labels,
                    "datasets": [{"label": "Comptes cumulés", "data": data}],
                },
            }
        )

        labels, data = _cumulative_monthly(Survey.objects.filter(is_active=True))
        stats.append(
            {
                "id": "active-surveys",
                "type": "line",
                "title": "Enquétes actives",
                "description": "Nombre cumulatif d'enquêtes actives, par mois de création.",
                "data": {
                    "labels": labels,
                    "datasets": [{"label": "Enquêtes cumulés", "data": data}],
                },
            }
        )

        labels, data = _cumulative_monthly(SurveyResponse.objects.filter(is_active=True))
        stats.append(
            {
                "id": "active-responses",
                "type": "line",
                "title": "Observations",
                "description": "Nombre cumulatif d'observations, par mois de création.",
                "data": {
                    "labels": labels,
                    "datasets": [{"label": "Observations cumulées", "data": data}],
                },
            }
        )

        return Response(stats)
