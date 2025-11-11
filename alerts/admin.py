from django.contrib import admin
from .models import Alert

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("id", "track_id", "duration", "created_at")
    list_filter = ("created_at",)