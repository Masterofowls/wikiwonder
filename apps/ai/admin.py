from django.contrib import admin

from apps.ai.models import AIUsageDaily


@admin.register(AIUsageDaily)
class AIUsageDailyAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "request_count")
    list_filter = ("date",)
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user", "date", "request_count")
