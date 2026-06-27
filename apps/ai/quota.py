"""Daily AI request quota (10 free viewer requests per user per day)."""
from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from apps.ai.models import AIUsageDaily


class QuotaExceededError(Exception):
    def __init__(self, remaining: int, limit: int):
        self.remaining = remaining
        self.limit = limit
        super().__init__(f"Daily AI limit reached ({limit}/day)")


def daily_limit() -> int:
    return int(getattr(settings, "AI_DAILY_REQUEST_LIMIT", 10))


def bypass_quota(user) -> bool:
    return bool(user and user.is_authenticated and user.is_staff)


def get_today_count(user) -> int:
    if not user or not user.is_authenticated:
        return 0
    row, _ = AIUsageDaily.objects.get_or_create(
        user=user,
        date=timezone.localdate(),
        defaults={"request_count": 0},
    )
    return row.request_count


def remaining_requests(user) -> int | None:
    """Return remaining quota, or None when unlimited (staff)."""
    if bypass_quota(user):
        return None
    return max(0, daily_limit() - get_today_count(user))


def quota_status(user) -> dict:
    limit = daily_limit()
    if bypass_quota(user):
        return {"limit": limit, "used": get_today_count(user), "remaining": None, "unlimited": True}
    used = get_today_count(user)
    return {
        "limit": limit,
        "used": used,
        "remaining": max(0, limit - used),
        "unlimited": False,
    }


def consume_quota(user, *, amount: int = 1) -> None:
    if bypass_quota(user):
        return
    limit = daily_limit()
    row, _ = AIUsageDaily.objects.select_for_update().get_or_create(
        user=user,
        date=timezone.localdate(),
        defaults={"request_count": 0},
    )
    if row.request_count + amount > limit:
        raise QuotaExceededError(remaining=max(0, limit - row.request_count), limit=limit)
    row.request_count += amount
    row.save(update_fields=["request_count"])
