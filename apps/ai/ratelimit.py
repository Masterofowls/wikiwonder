"""Burst rate limiting for AI endpoints (hourly cap per user)."""
from django.conf import settings
from django.core.cache import cache


class AIRateLimitError(Exception):
    def __init__(self, retry_after: int = 3600):
        self.retry_after = retry_after
        super().__init__("Too many AI requests. Please try again later.")


def check_ai_burst_rate(user) -> None:
    if not user.is_authenticated or user.is_staff:
        return
    limit = getattr(settings, "AI_BURST_HOURLY_LIMIT", 60)
    key = f"ai_burst:{user.pk}"
    count = cache.get(key, 0)
    if count >= limit:
        raise AIRateLimitError()
    cache.set(key, count + 1, 3600)
