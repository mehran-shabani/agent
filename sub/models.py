"""
Minimal subscription models used for testing the medagent application.

A SubscriptionPlan represents purchasable plans with a duration and price.
A Subscription associates a user with a plan and uses start/end dates to
determine whether it is active.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class CustomUser(AbstractUser):
    is_doctor = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class SubscriptionPlan(models.Model):
    """
    Represents a purchasable subscription plan. Each plan has a duration in days
    and a price. For example, a 31-day plan might cost 300 units.
    """
    name = models.CharField(max_length=50)
    days = models.PositiveIntegerField(help_text="Duration of the subscription in days")
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} ({self.days}d, {self.price})"

class Subscription(models.Model):
    """
    Associates a user with a subscription plan and keeps track of start and end dates.

    A subscription is considered active if the current time is before the end_date.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()

    def __str__(self):
        return f"Subscription({self.user.username}, plan={self.plan}, active={self.is_active})"

    @property
    def is_active(self) -> bool:
        return timezone.now() <= self.end_date
