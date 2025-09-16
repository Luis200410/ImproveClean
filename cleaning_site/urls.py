"""cleaning_site URL Configuration."""

from django.urls import include, path

from scheduler.admin import admin_site

urlpatterns = [
    path("admin/", admin_site.urls),
    path("", include("scheduler.urls")),
]
