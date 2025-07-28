"""
URL configuration for the medagent project used in testing.

This file routes requests to the medagent API endpoints and the Django admin.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('medagent.roots')),
]
