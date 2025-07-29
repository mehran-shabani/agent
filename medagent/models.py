"""
Data models for the MedAgent application.

These models capture the domain of a telemedicine chat system. They include
profiles for patients, chat sessions and messages, one-time OTP verifications,
access history logs, and session summaries. Historical records are tracked
using django-simple-history where appropriate.
"""

import hashlib
import datetime
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from simple_history.models import HistoricalRecords

User = get_user_model()

class PatientProfile(models.Model):
    """A medical profile for a user, separate from any role the user may have."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    national_code = models.CharField(max_length=10, unique=True)
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.username} ({self.national_code})"

class PatientSummary(models.Model):
    patient = models.OneToOneField(PatientProfile, on_delete=models.CASCADE)
    json_data = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"Summary for {self.patient}"

class OTPVerification(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    code_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    @classmethod
    def create(cls, patient, raw_code: str, minutes: int = 10):
        """Create a new OTP for the given patient, hashing the provided code."""
        return cls.objects.create(
            patient=patient,
            code_hash=hashlib.sha256(raw_code.encode()).hexdigest(),
            expires_at=timezone.now() + datetime.timedelta(minutes=minutes),
        )

    def valid(self, raw_code: str) -> bool:
        """
        Validate the provided raw code against the stored hash and expiration.

        Returns True if the current time is before expires_at and the hashes match.
        """
        return (
            timezone.now() < self.expires_at and
            hashlib.sha256(raw_code.encode()).hexdigest() == self.code_hash
        )

class AccessHistory(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_logs')
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    accessed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.doctor} accessed {self.patient} at {self.accessed_at}"

class ChatSession(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    purpose = models.CharField(max_length=120, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Session {self.id} ({self.owner} → {self.patient})"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=[('owner', 'owner'), ('assistant', 'assistant')])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"[{self.role}] {self.content[:30]}..."

class SessionSummary(models.Model):
    session = models.OneToOneField(ChatSession, on_delete=models.CASCADE)
    text_summary = models.TextField()
    json_summary = models.JSONField(default=dict)
    tokens_used = models.PositiveIntegerField()
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Summary for session {self.session_id}"
