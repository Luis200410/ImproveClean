from datetime import datetime, timedelta

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, F, Q
from django.db.models.expressions import ExpressionWrapper
from django.db.models.fields import DurationField
from django.db.models.functions import ExtractHour, ExtractWeekDay, TruncWeek
from django.utils import timezone

from .models import AdminPageView, Application, Booking, Worker, SERVICE_CHOICES


class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "service_type",
        "user",
        "scheduled_for",
        "status",
        "worker_response",
        "created_at",
    )
    list_filter = ("status", "worker_response", "service_type")
    search_fields = ("user__username", "address", "service_type")
    ordering = ("-scheduled_for",)


class WorkerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "service_focus",
        "experience_years",
        "contact_email",
        "phone_number",
        "is_active",
    )
    list_filter = ("service_focus", "is_active")
    search_fields = ("name", "headline", "contact_email", "phone_number")
    change_form_template = "admin/scheduler/worker/change_form.html"

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        upcoming = []
        past_due = []
        week_days = []
        week_total = 0
        if object_id:
            now = timezone.now()
            schedule_qs = (
                Booking.objects.filter(worker_id=object_id)
                .select_related("user")
                .order_by("scheduled_for")
            )
            upcoming = schedule_qs.filter(scheduled_for__gte=now)[:20]
            past_due = schedule_qs.filter(scheduled_for__lt=now).order_by("-scheduled_for")[:10]

            local_now = timezone.localtime(now)
            start_week_date = local_now.date() - timedelta(days=local_now.weekday())
            tz = timezone.get_current_timezone()
            start_of_week = timezone.make_aware(
                datetime.combine(start_week_date, datetime.min.time()), tz
            )
            end_of_week = start_of_week + timedelta(days=7)
            calendar_dates = [start_week_date + timedelta(days=i) for i in range(7)]
            week_day_map = {day: [] for day in calendar_dates}

            weekly_qs = schedule_qs.filter(
                scheduled_for__gte=start_of_week, scheduled_for__lt=end_of_week
            )
            for booking in weekly_qs:
                local_date = timezone.localtime(booking.scheduled_for).date()
                week_day_map.setdefault(local_date, []).append(booking)
                week_total += 1

            week_days = [{"date": day, "bookings": week_day_map.get(day, [])} for day in calendar_dates]
        extra_context.update(
            {
                "worker_upcoming_schedule": upcoming,
                "worker_recent_history": past_due,
                "worker_week_days": week_days,
                "worker_week_total": week_total,
            }
        )
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "created_at", "reviewed")
    list_filter = ("reviewed", "created_at")
    search_fields = ("full_name", "email", "phone", "experience")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


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
        last_7 = now - timedelta(days=7)

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

        created_last_7 = bookings_qs.filter(created_at__gte=last_7).count()
        created_last_30 = bookings_qs.filter(created_at__gte=last_30).count()

        recent_period = bookings_qs.filter(scheduled_for__gte=last_30)
        recent_total = recent_period.count()
        recent_completed = recent_period.filter(status="completed").count()
        recent_cancelled = recent_period.filter(status="cancelled").count()
        recent_completion_rate = (
            round((recent_completed / recent_total) * 100, 1) if recent_total else 0
        )
        recent_cancellation_rate = (
            round((recent_cancelled / recent_total) * 100, 1) if recent_total else 0
        )

        rush_total = bookings_qs.filter(rush_cleaning=True).count()
        upcoming_qs = bookings_qs.filter(scheduled_for__range=(now, next_week)).order_by(
            "scheduled_for"
        )
        upcoming = list(upcoming_qs[:8])
        upcoming_unassigned = upcoming_qs.filter(worker__isnull=True).count()
        unassigned_total = bookings_qs.filter(worker__isnull=True).count()

        lead_agg = (
            bookings_qs.exclude(created_at__isnull=True)
            .annotate(
                lead_delta=ExpressionWrapper(
                    F("scheduled_for") - F("created_at"), output_field=DurationField()
                )
            )
            .aggregate(avg_lead=Avg("lead_delta"))
        )
        avg_lead_seconds = lead_agg["avg_lead"].total_seconds() if lead_agg["avg_lead"] else 0
        avg_lead_days = round(avg_lead_seconds / 86400, 1) if avg_lead_seconds else 0

        worker_rankings = (
            Worker.objects.filter(is_active=True)
            .annotate(
                booking_total=Count("bookings"),
                upcoming_total=Count(
                    "bookings",
                    filter=Q(bookings__scheduled_for__range=(now, next_week)),
                ),
            )
            .order_by("-booking_total", "name")[:6]
        )

        worker_utilization_qs = (
            Worker.objects.filter(is_active=True)
            .annotate(
                upcoming_total=Count(
                    "bookings",
                    filter=Q(bookings__scheduled_for__range=(now, next_week)),
                ),
                lifetime_total=Count("bookings"),
            )
            .order_by("name")
        )
        worker_utilization = list(worker_utilization_qs)
        idle_workers = [worker for worker in worker_utilization if worker.upcoming_total == 0]

        assigned_next_week = (
            upcoming_qs.filter(worker__isnull=False)
            .select_related("worker", "user")
            .order_by("worker__name", "scheduled_for")
        )
        worker_schedules = []
        schedule_map = {}
        for worker in worker_utilization:
            entry = {"worker": worker, "bookings": []}
            worker_schedules.append(entry)
            schedule_map[worker.id] = entry
        for booking in assigned_next_week:
            entry = schedule_map.get(booking.worker_id)
            if entry is None:
                entry = {"worker": booking.worker, "bookings": []}
                worker_schedules.append(entry)
                schedule_map[booking.worker_id] = entry
            entry["bookings"].append(booking)

        User = get_user_model()
        new_users = User.objects.filter(date_joined__gte=last_30).count()
        total_clients = bookings_qs.values("user").distinct().count()
        repeat_clients = (
            bookings_qs.values("user").annotate(total=Count("id")).filter(total__gt=1).count()
        )
        repeat_rate = round((repeat_clients / total_clients) * 100, 1) if total_clients else 0
        new_client_cancellations = bookings_qs.filter(
            status="cancelled", user__date_joined__gte=last_30
        ).count()
        new_client_bookings = bookings_qs.filter(user__date_joined__gte=last_30).count()
        new_client_cancellation_rate = (
            round((new_client_cancellations / new_client_bookings) * 100, 1)
            if new_client_bookings
            else 0
        )

        recent_bookings = bookings_qs.filter(scheduled_for__gte=last_30)
        weekday_lookup = [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]
        weekday_data = {
            row["weekday"]: row["total"]
            for row in recent_bookings.annotate(weekday=ExtractWeekDay("scheduled_for")).values("weekday").annotate(total=Count("id"))
        }
        weekday_mix = [
            {"label": weekday_lookup[i - 1], "total": weekday_data.get(i, 0)}
            for i in range(1, 8)
        ]
        weekday_peak = max((item["total"] for item in weekday_mix), default=0)

        hour_data = {
            row["hour"]: row["total"]
            for row in recent_bookings.annotate(hour=ExtractHour("scheduled_for")).values("hour").annotate(total=Count("id"))
        }
        hourly_mix = [
            {"label": f"{hour:02d}:00", "total": hour_data.get(hour, 0)}
            for hour in range(0, 24)
        ]
        hourly_peak = max((item["total"] for item in hourly_mix), default=0)

        rush_trend = []
        trend_start = now - timedelta(weeks=12)
        weekly_rush = (
            bookings_qs.filter(created_at__gte=trend_start)
            .annotate(week=TruncWeek("created_at"))
            .values("week")
            .annotate(
                total=Count("id"),
                rush=Count("id", filter=Q(rush_cleaning=True)),
            )
            .order_by("week")
        )
        for row in weekly_rush:
            ratio = round((row["rush"] / row["total"]) * 100, 1) if row["total"] else 0
            rush_trend.append({"week": row["week"], "total": row["total"], "rush": row["rush"], "ratio": ratio})

        # Track admin dashboard page views, similar to an on-page SEO report
        if request.method == "GET":
            session_key = request.session.session_key or ""
            if not request.session.session_key:
                request.session.save()
                session_key = request.session.session_key or ""
            AdminPageView.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=session_key or "",
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
                path=request.path,
            )

        page_views_qs = AdminPageView.objects.filter(path=request.path)
        page_view_total = page_views_qs.count()
        page_view_30 = page_views_qs.filter(viewed_at__gte=last_30).count()
        page_view_7 = page_views_qs.filter(viewed_at__gte=last_7).count()
        unique_admins_30 = (
            page_views_qs.filter(viewed_at__gte=last_30, user__isnull=False)
            .values("user")
            .distinct()
            .count()
        )
        unique_sessions_30 = (
            page_views_qs.filter(viewed_at__gte=last_30)
            .exclude(session_key="")
            .values("session_key")
            .distinct()
            .count()
        )
        last_page_view = page_views_qs.order_by("-viewed_at").first()

        extra_context.update(
            {
                "total_bookings": total_bookings,
                "status_summary": status_summary,
                "service_summary": service_summary,
                "rush_total": rush_total,
                "upcoming": upcoming,
                "worker_rankings": worker_rankings,
                "new_users": new_users,
                "created_last_7": created_last_7,
                "created_last_30": created_last_30,
                "recent_completion_rate": recent_completion_rate,
                "recent_cancellation_rate": recent_cancellation_rate,
                "recent_completed": recent_completed,
                "recent_cancelled": recent_cancelled,
                "unassigned_total": unassigned_total,
                "upcoming_unassigned": upcoming_unassigned,
                "avg_lead_days": avg_lead_days,
                "repeat_rate": repeat_rate,
                "repeat_clients": repeat_clients,
                "total_clients": total_clients,
                "new_client_cancellations": new_client_cancellations,
                "new_client_cancellation_rate": new_client_cancellation_rate,
                "worker_utilization": worker_utilization,
                "idle_workers": idle_workers,
                "worker_schedules": worker_schedules,
                "weekday_mix": weekday_mix,
                "weekday_peak": weekday_peak,
                "hourly_mix": hourly_mix,
                "hourly_peak": hourly_peak,
                "rush_trend": rush_trend,
                "page_view_total": page_view_total,
                "page_view_30": page_view_30,
                "page_view_7": page_view_7,
                "unique_admins_30": unique_admins_30,
                "unique_sessions_30": unique_sessions_30,
                "last_page_view": last_page_view,
            }
        )

        return super().index(request, extra_context=extra_context)


admin_site = SuperuserAdminSite(name="superuser_admin")
admin_site.register(Booking, BookingAdmin)
admin_site.register(Worker, WorkerAdmin)
