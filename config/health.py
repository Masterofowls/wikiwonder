from django.db import connection
from django.http import JsonResponse
from django.views import View


class HealthView(View):
    """Liveness probe — always 200 so Fly routing works during DB warmup."""

    def get(self, request):
        db_ok = True
        db_error = None
        try:
            connection.ensure_connection()
        except Exception as exc:
            db_ok = False
            db_error = str(exc)

        return JsonResponse(
            {
                "status": "healthy" if db_ok else "degraded",
                "database": "ok" if db_ok else db_error,
            },
            status=200,
        )
