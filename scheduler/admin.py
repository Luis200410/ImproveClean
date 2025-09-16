from django.contrib import admin
from django.contrib.admin import AdminSite

from .models import Booking


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


class SuperuserAdminSite(AdminSite):
    site_header = "ImproveClean Administration"
    site_title = "ImproveClean Admin"
    index_title = "Superuser Controls"

    def has_permission(self, request):
        return bool(request.user and request.user.is_active and request.user.is_superuser)


admin_site = SuperuserAdminSite(name="superuser_admin")
admin_site.register(Booking, BookingAdmin)
