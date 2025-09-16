from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from .forms import BookingForm, SignupForm, StyledAuthenticationForm
from .models import Booking, SERVICE_CHOICES, Worker


class LandingView(TemplateView):
    template_name = "scheduler/landing.html"


class AboutView(TemplateView):
    template_name = "scheduler/about.html"


class ServicesView(TemplateView):
    template_name = "scheduler/services.html"


class AccountView(LoginRequiredMixin, TemplateView):
    template_name = "scheduler/account.html"


class RegisterView(FormView):
    form_class = SignupForm
    template_name = "scheduler/register.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(
            self.request,
            "Welcome to ImproveClean! Your account is ready and you can schedule cleanings immediately.",
        )
        return super().form_valid(form)


class AuthLoginView(LoginView):
    template_name = "scheduler/login.html"
    authentication_form = StyledAuthenticationForm

    def form_valid(self, form):
        messages.success(self.request, "Successfully signed in.")
        return super().form_valid(form)


class AuthLogoutView(LogoutView):
    next_page = reverse_lazy("landing")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "scheduler/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bookings = (
            self.request.user.bookings.select_related("worker").all()
        )
        context["bookings"] = bookings

        form = kwargs.get("form") or BookingForm()
        context["form"] = form

        selected_worker_id = form["worker"].value()
        service_focus = self.request.GET.get("team_service")
        search_query = self.request.GET.get("team_search", "").strip()

        workers = Worker.objects.filter(is_active=True)
        if service_focus:
            workers = workers.filter(service_focus=service_focus)
        if search_query:
            workers = workers.filter(name__icontains=search_query)
        if selected_worker_id:
            workers = workers | Worker.objects.filter(pk=selected_worker_id)
        workers = workers.distinct().order_by("name")

        context.update(
            {
                "workers": workers,
                "team_service": service_focus or "",
                "team_search": search_query,
                "service_choices": SERVICE_CHOICES,
                "selected_worker_id": selected_worker_id,
                "rush_threshold_hours": 5,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            rush_threshold = timezone.now() + timedelta(hours=5)
            booking.rush_cleaning = booking.scheduled_for <= rush_threshold
            booking.save()
            worker_text = (
                f" with {booking.worker.name}" if booking.worker else ""
            )
            rush_text = (
                " Rush service applied automatically based on your requested time."
                if booking.rush_cleaning
                else ""
            )
            messages.success(
                request,
                "Your cleaning has been scheduled"
                f"{worker_text}. Our team will confirm the details shortly.{rush_text}",
            )
            return redirect("dashboard")
        messages.error(request, "Please correct the highlighted errors to book your cleaning.")
        return self.render_to_response(self.get_context_data(form=form))


@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if request.method == "POST":
        booking.status = "cancelled"
        booking.save(update_fields=["status"])
        messages.info(request, "The booking has been cancelled.")
    return redirect("dashboard")
