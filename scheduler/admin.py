from django.contrib import admin
from django.contrib.admin import AdminSite

from .models import Booking, Worker


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


class WorkerAdmin(admin.ModelAdmin):
    list_display = ("name", "service_focus", "experience_years", "is_active")
    list_filter = ("service_focus", "is_active")
    search_fields = ("name", "headline")


class SuperuserAdminSite(AdminSite):
    site_header = "ImproveClean Administration"
    site_title = "ImproveClean Admin"
    index_title = "Superuser Controls"

    def has_permission(self, request):
        return bool(request.user and request.user.is_active and request.user.is_superuser)


admin_site = SuperuserAdminSite(name="superuser_admin")
admin_site.register(Booking, BookingAdmin)
admin_site.register(Worker, WorkerAdmin)
