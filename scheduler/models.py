from django.conf import settings
from django.db import models


SERVICE_CHOICES = [
    ("standard", "Standard Cleaning"),
    ("deep", "Deep Cleaning"),
    ("move_out", "Move In/Out"),
    ("office", "Office Cleaning"),
]


class Worker(models.Model):
    """A professional cleaner that clients can request."""

    name = models.CharField(max_length=120)
    headline = models.CharField(max_length=150, blank=True)
    service_focus = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    experience_years = models.PositiveIntegerField(default=1)
    photo_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Booking(models.Model):
    """A scheduled cleaning appointment tied to a user."""

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    WORKER_RESPONSE_CHOICES = [
        ("pending", "Awaiting Response"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    scheduled_for = models.DateTimeField()
    address = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    worker = models.ForeignKey(
        "Worker",
        on_delete=models.SET_NULL,
        related_name="bookings",
        null=True,
        blank=True,
    )
    rush_cleaning = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="scheduled"
    )
    worker_response = models.CharField(
        max_length=20, choices=WORKER_RESPONSE_CHOICES, default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_for"]

    def __str__(self) -> str:
        worker_name = f" with {self.worker.name}" if self.worker else ""
        return (
            f"{self.get_service_type_display()} on {self.scheduled_for:%Y-%m-%d %H:%M}{worker_name}"
        )


class AdminPageView(models.Model):
    """Lightweight page view tracker for the concierge admin dashboard."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_page_views",
    )
    session_key = models.CharField(max_length=40, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    path = models.CharField(max_length=255)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["viewed_at"])]
        ordering = ["-viewed_at"]

    def __str__(self) -> str:
        who = self.user.get_username() if self.user else "anonymous"
        return f"{who} viewed {self.path} at {self.viewed_at:%Y-%m-%d %H:%M:%S}"


class Application(models.Model):
    """Inbound application from the Work With Us form."""

    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    experience = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"
