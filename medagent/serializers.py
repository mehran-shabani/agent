"""
Serializers for the MedAgent REST API.

These serializers validate incoming data and translate model instances into
primitive representations. They are used by the API views to ensure that
requests contain valid fields and to structure responses.
"""

from rest_framework import serializers
from medagent.models import (
    PatientProfile, ChatSession, ChatMessage,
    SessionSummary, PatientSummary
)

class OTPRequestSerializer(serializers.Serializer):
    national_code = serializers.CharField(max_length=10)

class OTPVerifySerializer(serializers.Serializer):
    national_code = serializers.CharField(max_length=10)
    code = serializers.CharField(max_length=6)

class CreateSessionSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
    purpose = serializers.CharField(
        max_length=120,
        allow_blank=True,
        required=False,        # ← فیلد اختیاری شد
        default=""
    )


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "session", "role", "content", "created_at"]
        read_only_fields = ["role", "created_at"]

class EndSessionSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()

class PatientSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientSummary
        fields = ["json_data", "updated_at"]

class SessionSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionSummary
        fields = ["text_summary", "json_summary", "tokens_used", "generated_at"]
