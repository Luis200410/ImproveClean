from django.urls import path

from .views import (
    AboutView,
    AccountView,
    AuthLoginView,
    AuthLogoutView,
    DashboardView,
    LandingView,
    RegisterView,
    ServicesView,
    WorkerBookingDetailView,
    WorkWithUsView,
    cancel_booking,
)

urlpatterns = [
    path("", LandingView.as_view(), name="landing"),
    path("about/", AboutView.as_view(), name="about"),
    path("services/", ServicesView.as_view(), name="services"),
    path("account/", AccountView.as_view(), name="account"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", AuthLoginView.as_view(), name="login"),
    path("logout/", AuthLogoutView.as_view(), name="logout"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("bookings/<int:pk>/cancel/", cancel_booking, name="cancel_booking"),
    path(
        "worker/bookings/<int:pk>/",
        WorkerBookingDetailView.as_view(),
        name="worker_booking_detail",
    ),
    path("work-with-us/", WorkWithUsView.as_view(), name="work_with_us"),
]
