from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "service_type",
        "user",
        "scheduled_for",
        "status",
        "created_at",
    )
    list_filter = ("status", "service_type")
    search_fields = ("user__username", "address", "service_type")
    ordering = ("-scheduled_for",)
