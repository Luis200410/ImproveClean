from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from .forms import BookingForm, SignupForm, StyledAuthenticationForm
from .models import Booking


class LandingView(TemplateView):
    template_name = "scheduler/landing.html"


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
        context["bookings"] = self.request.user.bookings.all()
        context["form"] = kwargs.get("form") or BookingForm()
        return context

    def post(self, request, *args, **kwargs):
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.save()
            messages.success(
                request,
                "Your cleaning has been scheduled. Our team will confirm the details shortly.",
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
