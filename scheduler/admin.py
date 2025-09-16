from datetime import timedelta

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

from .models import Booking, Worker, SERVICE_CHOICES


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
    index_template = "admin/custom_index.html"

    def has_permission(self, request):
        return bool(request.user and request.user.is_active and request.user.is_superuser)

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        now = timezone.now()
        next_week = now + timedelta(days=7)
        last_30 = now - timedelta(days=30)

        bookings_qs = Booking.objects.select_related("worker", "user")
        total_bookings = bookings_qs.count()
        status_map = {key: 0 for key, _ in Booking.STATUS_CHOICES}
        for row in bookings_qs.values("status").annotate(total=Count("id")):
            status_map[row["status"]] = row["total"]
        status_summary = []
        for code, label in Booking.STATUS_CHOICES:
            total = status_map.get(code, 0)
            percent = round((total / total_bookings) * 100, 1) if total_bookings else 0
            status_summary.append({"code": code, "label": label, "total": total, "percent": percent})

        service_map = {key: 0 for key, _ in SERVICE_CHOICES}
        for row in bookings_qs.values("service_type").annotate(total=Count("id")):
            service_map[row["service_type"]] = row["total"]
        service_summary = []
        for code, label in SERVICE_CHOICES:
            total = service_map.get(code, 0)
            service_summary.append({"code": code, "label": label, "total": total})

        rush_total = bookings_qs.filter(rush_cleaning=True).count()
        upcoming = bookings_qs.filter(scheduled_for__range=(now, next_week)).order_by("scheduled_for")[:8]

        worker_rankings = (
            Worker.objects.filter(is_active=True)
            .annotate(booking_total=Count("bookings"))
            .order_by("-booking_total", "name")[:6]
        )

        User = get_user_model()
        new_users = User.objects.filter(date_joined__gte=last_30).count()

        extra_context.update(
            {
                "total_bookings": total_bookings,
                "status_summary": status_summary,
                "service_summary": service_summary,
                "rush_total": rush_total,
                "upcoming": upcoming,
                "worker_rankings": worker_rankings,
                "new_users": new_users,
            }
        )

        return super().index(request, extra_context=extra_context)


admin_site = SuperuserAdminSite(name="superuser_admin")
admin_site.register(Booking, BookingAdmin)
admin_site.register(Worker, WorkerAdmin)
