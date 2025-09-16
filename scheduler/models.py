from django.conf import settings
from django.db import models


class Booking(models.Model):
    """A scheduled cleaning appointment tied to a user."""

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    service_type = models.CharField(max_length=100)
    scheduled_for = models.DateTimeField()
    address = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="scheduled"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_for"]

    def __str__(self) -> str:
        return f"{self.service_type} on {self.scheduled_for:%Y-%m-%d %H:%M}"
