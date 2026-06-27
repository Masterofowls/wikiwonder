"""Track daily AI request usage per user."""
from django.conf import settings
from django.db import models


class AIUsageDaily(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_usage_days",
    )
    date = models.DateField(db_index=True)
    request_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("user", "date")]
        indexes = [models.Index(fields=["user", "date"])]
        verbose_name = "AI daily usage"
        verbose_name_plural = "AI daily usage"

    def __str__(self) -> str:
        return f"{self.user_id} @ {self.date}: {self.request_count}"
