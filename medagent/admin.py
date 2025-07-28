"""
Admin configuration for MedAgent models.

Registers relevant models with the Django admin site. Historical records
provided by simple_history are displayed for select models.
"""

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from medagent.models import (
    PatientProfile, PatientSummary, OTPVerification,
    AccessHistory, ChatSession, ChatMessage, SessionSummary
)

admin.site.register(PatientProfile)
admin.site.register(PatientSummary, SimpleHistoryAdmin)
admin.site.register(OTPVerification)
admin.site.register(AccessHistory)
admin.site.register(ChatSession)
admin.site.register(ChatMessage, SimpleHistoryAdmin)
admin.site.register(SessionSummary)
