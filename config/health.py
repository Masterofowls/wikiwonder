from pathlib import Path

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views import View


class HealthView(View):
    """Liveness probe with DB and media volume checks."""

    def get(self, request):
        db_ok = True
        db_error = None
        try:
            connection.ensure_connection()
        except Exception as exc:
            db_ok = False
            db_error = str(exc)

        media_ok = True
        media_error = None
        if getattr(settings, "SERVE_MEDIA", True):
            try:
                media_root = Path(settings.MEDIA_ROOT)
                media_root.mkdir(parents=True, exist_ok=True)
                probe = media_root / ".health_probe"
                probe.write_text("ok", encoding="utf-8")
                probe.unlink(missing_ok=True)
            except Exception as exc:
                media_ok = False
                media_error = str(exc)

        healthy = db_ok and media_ok
        return JsonResponse(
            {
                "status": "healthy" if healthy else "degraded",
                "database": "ok" if db_ok else db_error,
                "media": "ok" if media_ok else media_error,
            },
            status=200,
        )
