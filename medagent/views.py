"""
REST API views for the MedAgent application.

These views implement OTP request/verification, chat session management, posting
messages, ending sessions, and retrieving summaries. The views enforce
authentication and subscription permissions where appropriate and rely on
auxiliary modules for sending SMS and interacting with the agent.
"""

import random
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from medagent.permissions import HasActiveSubscription
from medagent.serializers import (
    OTPRequestSerializer, OTPVerifySerializer,
    CreateSessionSerializer, ChatMessageSerializer,
    EndSessionSerializer, PatientSummarySerializer,
    SessionSummarySerializer
)
from medagent.models import (
    PatientProfile, OTPVerification, AccessHistory,
    ChatSession, ChatMessage, SessionSummary, PatientSummary
)
from medagent.sms import send_sms
from medagent.tools import SummarizeSessionTool, ProfanityCheckTool

class RequestOTP(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription]

    def post(self, request):
        ser = OTPRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        nc = ser.validated_data["national_code"]

        patient = get_object_or_404(PatientProfile, national_code=nc)
        raw = f"{random.randint(0, 999999):06d}"
        OTPVerification.create(patient, raw)
        send_sms(patient.phone_number, f"کد دسترسی شما: {raw}")
        return Response({"msg": "OTP sent"}, status=200)

class VerifyOTP(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription]

    def post(self, request):
        ser = OTPVerifySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        nc, code = ser.validated_data.values()

        patient = get_object_or_404(PatientProfile, national_code=nc)
        otp = OTPVerification.objects.filter(patient=patient).latest("created_at")
        if not otp.valid(code) and AccessHistory.objects.filter(doctor=request.user, patient=patient).exists():
            return Response({"error": "OTP نامعتبر یا منقضی"}, status=400)

        AccessHistory.objects.create(doctor=request.user, patient=patient)
        return Response({"msg": "Access granted", "patient_id": patient.id}, status=200)

class CreateSession(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription]

    def post(self, request):
        ser = CreateSessionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        patient = get_object_or_404(PatientProfile, id=ser.validated_data["patient_id"])

        # تشخیص پزشک با بررسی عضویت در گروه doctor
        is_doctor = request.user.groups.filter(name__iexact="doctor").exists()
        if is_doctor and patient.user != request.user:
            if not AccessHistory.objects.filter(doctor=request.user, patient=patient).exists():
                return Response({"error": "no OTP access"}, status=403)

        session = ChatSession.objects.create(
            owner=request.user,
            patient=patient,
            purpose=ser.validated_data.get("purpose", "")
        )
        return Response({"session_id": session.id}, status=201)

class PostMessage(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription]

    def post(self, request, session_id):
        session = get_object_or_404(ChatSession, id=session_id, ended_at__isnull=True)
        if session.owner != request.user:
            return Response({"error": "not owner"}, status=403)

        ser = ChatMessageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        content = ser.validated_data["content"]

        # Check for profanity
        if ProfanityCheckTool()._run(content) == "True":
            content = "[پیام حاوی کلمات نامناسب بود]"

        ChatMessage.objects.create(session=session, role="owner", content=content)
        from medagent.agent_setup import agent

        
        reply = agent.run(content)
        ChatMessage.objects.create(session=session, role="assistant", content=reply)
        return Response({"assistant_reply": reply})

class EndSession(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription]

    def patch(self, request):
        ser = EndSessionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sess = get_object_or_404(ChatSession, id=ser.validated_data["session_id"], owner=request.user)

        sess.ended_at = timezone.now()
        sess.save(update_fields=["ended_at"])

        SummarizeSessionTool()._run(str(sess.id))
        return Response({"msg": "session closed & summarized"})

class GetPatientSummary(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription]

    def get(self, request, patient_id):
        summary = get_object_or_404(PatientSummary, patient_id=patient_id)
        patient_user = summary.patient.user
        # فقط خود بیمار یا پزشکی که OTP دارد می‌تواند خلاصه را ببیند
        if request.user != patient_user and not AccessHistory.objects.filter(doctor=request.user, patient=summary.patient).exists():
            return Response({"error": "access denied"}, status=403)
        return Response(PatientSummarySerializer(summary).data)

class GetSessionSummary(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription]

    def get(self, request, session_id):
        summ = get_object_or_404(SessionSummary, session_id=session_id)
        session = summ.session
        # مالک جلسه یا پزشکی با دسترسی OTP می‌تواند خلاصه را ببیند
        if request.user != session.owner and not AccessHistory.objects.filter(doctor=request.user, patient=session.patient).exists():
            return Response({"error": "access denied"}, status=403)
        return Response(SessionSummarySerializer(summ).data)
