from django.db import connection
from django.http import JsonResponse
from django.views import View


class HealthView(View):
    def get(self, request):
        try:
            connection.ensure_connection()
            db_ok = True
        except Exception as exc:
            db_ok = False
            db_error = str(exc)
        else:
            db_error = None

        status = 200 if db_ok else 503
        return JsonResponse(
            {
                "status": "healthy" if db_ok else "unhealthy",
                "database": "ok" if db_ok else db_error,
            },
            status=status,
        )
