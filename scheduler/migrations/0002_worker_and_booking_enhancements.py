import django.db.models.deletion
from django.db import migrations, models

import scheduler.models


class Migration(migrations.Migration):

    dependencies = [
        ("scheduler", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Worker",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("headline", models.CharField(blank=True, max_length=150)),
                (
                    "service_focus",
                    models.CharField(choices=scheduler.models.SERVICE_CHOICES, max_length=50),
                ),
                ("experience_years", models.PositiveIntegerField(default=1)),
                ("photo_url", models.URLField(blank=True)),
                ("bio", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="booking",
            name="rush_cleaning",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="booking",
            name="worker",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="bookings",
                to="scheduler.worker",
            ),
        ),
        migrations.AlterField(
            model_name="booking",
            name="service_type",
            field=models.CharField(
                choices=scheduler.models.SERVICE_CHOICES, max_length=50
            ),
        ),
    ]
