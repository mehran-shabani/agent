import json
import random
import datetime

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.test import APIClient

from medagent.models import PatientProfile, OTPVerification, AccessHistory, ChatSession, ChatMessage, SessionSummary, PatientSummary
from sub.models import SubscriptionPlan, Subscription

User = get_user_model()

@pytest.fixture
def api_client(db):
    return APIClient()

@pytest.fixture
def subscription_plan(db):
    # Create three subscription plans as requested: 31, 93, 186 days with prices
    p1 = SubscriptionPlan.objects.create(name="31-day", days=31, price=300)
    p2 = SubscriptionPlan.objects.create(name="93-day", days=93, price=890)
    p3 = SubscriptionPlan.objects.create(name="186-day", days=186, price=1790)
    return p1

def create_user_with_subscription(username, plan, days_offset=0, is_doctor=False):
    user = User.objects.create_user(username=username, password="pwd")
    if is_doctor:
        # Ensure a "doctor" group exists and add the user to it to simulate doctor role
        group, _ = Group.objects.get_or_create(name="doctor")
        user.groups.add(group)
    end_date = timezone.now() + datetime.timedelta(days=plan.days - days_offset)
    Subscription.objects.create(user=user, plan=plan, end_date=end_date)
    return user

@pytest.mark.django_db
def test_authentication_required(api_client):
    # Endpoints should reject unauthenticated requests
    response = api_client.post("/api/otp/request/", {"national_code": "1234567890"})
    assert response.status_code in {401, 403}

@pytest.mark.django_db
def test_otp_flow_for_active_subscription(monkeypatch, api_client, subscription_plan):
    # Setup user with active subscription and patient profile
    user = create_user_with_subscription("otpuser", subscription_plan)
    patient_profile = PatientProfile.objects.create(user=user, national_code="5555555555", phone_number="09120000007")
    api_client.force_authenticate(user=user)
    # Patch random.randint to return a predictable code
    monkeypatch.setattr(random, 'randint', lambda a, b: 123456)
    # Patch send_sms to avoid actual HTTP call
    monkeypatch.setattr("medagent.sms.send_sms", lambda phone, text, sender=None: True)
    # Request OTP
    response = api_client.post("/api/otp/request/", {"national_code": patient_profile.national_code})
    assert response.status_code == 200
    # Latest OTP saved in database
    otp = OTPVerification.objects.latest("created_at")
    assert otp.patient == patient_profile
    # Verify OTP
    response = api_client.post("/api/otp/verify/", {"national_code": patient_profile.national_code, "code": "123456"})
    assert response.status_code == 200
    assert AccessHistory.objects.filter(doctor=user, patient=patient_profile).exists()

@pytest.mark.django_db
def test_otp_request_denied_without_active_subscription(api_client, subscription_plan):
    # Create user with expired subscription
    user = create_user_with_subscription("expireduser", subscription_plan, days_offset=subscription_plan.days + 1)
    patient_profile = PatientProfile.objects.create(user=user, national_code="6666666666", phone_number="09120000008")
    api_client.force_authenticate(user=user)
    response = api_client.post("/api/otp/request/", {"national_code": patient_profile.national_code})
    # Should be denied due to permission
    assert response.status_code in {403, 401}

@pytest.mark.django_db
def test_create_session_flow_for_doctor_requires_otp(monkeypatch, api_client, subscription_plan):
    # Doctor and patient separate users
    doctor = create_user_with_subscription("doctor", subscription_plan, is_doctor=True)
    patient_user = create_user_with_subscription("patient", subscription_plan)
    patient_profile = PatientProfile.objects.create(user=patient_user, national_code="7777777777", phone_number="09120000009")
    api_client.force_authenticate(user=doctor)
    # Attempt to create session without OTP (no AccessHistory) should fail
    response = api_client.post("/api/session/create/", {"patient_id": patient_profile.id, "purpose": "Check"})
    assert response.status_code == 403
    # Grant access via AccessHistory (simulate OTP verification)
    AccessHistory.objects.create(doctor=doctor, patient=patient_profile)
    # Now creation should succeed
    response = api_client.post("/api/session/create/", {"patient_id": patient_profile.id, "purpose": "Check"})
    assert response.status_code == 201
    session_id = response.data["session_id"]
    assert ChatSession.objects.filter(id=session_id).exists()

@pytest.mark.django_db
def test_post_message_and_response(monkeypatch, api_client, subscription_plan):
    # Setup user and session
    user = create_user_with_subscription("poster", subscription_plan)
    profile = PatientProfile.objects.create(user=user, national_code="8888888888", phone_number="09120000010")
    api_client.force_authenticate(user=user)
    # Create session
    response = api_client.post("/api/session/create/", {"patient_id": profile.id})
    session_id = response.data["session_id"]
    # Patch ProfanityCheckTool and agent.run
    monkeypatch.setattr("medagent.tools.ProfanityCheckTool._run", lambda self, text: "False")
    monkeypatch.setattr("medagent.agent_setup.agent.run", lambda msg: "assistant reply")
    # Post a message
    response = api_client.post(f"/api/session/{session_id}/message/", {"session": session_id, "content": "Hello"})
    assert response.status_code == 200
    assert response.data["assistant_reply"] == "assistant reply"
    # Two messages should be stored in DB (owner and assistant)
    messages = ChatMessage.objects.filter(session_id=session_id)
    assert messages.count() == 2
    assert messages.filter(role="assistant").first().content == "assistant reply"

@pytest.mark.django_db
def test_post_message_with_profanity(monkeypatch, api_client, subscription_plan):
    # Setup user and session
    user = create_user_with_subscription("profuser", subscription_plan)
    profile = PatientProfile.objects.create(user=user, national_code="9999999999", phone_number="09120000011")
    api_client.force_authenticate(user=user)
    response = api_client.post("/api/session/create/", {"patient_id": profile.id})
    session_id = response.data["session_id"]
    # Force profanity detection to True
    monkeypatch.setattr("medagent.tools.ProfanityCheckTool._run", lambda self, text: "True")
    monkeypatch.setattr("medagent.agent_setup.agent.run", lambda msg: "clean reply")
    # Post a profane message
    response = api_client.post(f"/api/session/{session_id}/message/", {"session": session_id, "content": "bad words"})
    assert response.status_code == 200
    # Stored owner message should be sanitized
    msg = ChatMessage.objects.filter(session_id=session_id, role="owner").first()
    assert msg.content == "[پیام حاوی کلمات نامناسب بود]"

@pytest.mark.django_db
def test_end_session_and_summary(monkeypatch, api_client, subscription_plan):
    # Setup user and session
    user = create_user_with_subscription("enders", subscription_plan)
    profile = PatientProfile.objects.create(user=user, national_code="1212121212", phone_number="09120000012")
    api_client.force_authenticate(user=user)
    response = api_client.post("/api/session/create/", {"patient_id": profile.id})
    session_id = response.data["session_id"]
    # Add a message to session so that summary has content
    ChatMessage.objects.create(session_id=session_id, role="owner", content="Test")
    ChatMessage.objects.create(session_id=session_id, role="assistant", content="Reply")
    # Patch tb_chat to return JSON summary for summarization
    monkeypatch.setattr("medagent.talkbot_client.tb_chat", lambda messages, model="o3-mini": json.dumps({"text_summary": "summary", "token_count": 10}))
    # End session
    response = api_client.patch("/api/session/end/", {"session_id": session_id})
    assert response.status_code == 200
    session = ChatSession.objects.get(id=session_id)
    assert session.ended_at is not None
    summary = SessionSummary.objects.get(session_id=session_id)
    assert summary.text_summary == "summary"
    assert summary.tokens_used == 10

@pytest.mark.django_db
def test_get_summaries_and_patient_summary_endpoint(api_client, subscription_plan):
    # Setup user and patient summary
    user = create_user_with_subscription("sumend", subscription_plan)
    profile = PatientProfile.objects.create(user=user, national_code="2323232323", phone_number="09120000013")
    PatientSummary.objects.create(patient=profile, json_data={"a": 1})
    api_client.force_authenticate(user=user)
    # Get patient summary
    response = api_client.get(f"/api/patient/{profile.id}/summary/")
    assert response.status_code == 200
    assert response.data["json_data"] == {"a": 1}
    # Create session and session summary to test session summary endpoint
    session = ChatSession.objects.create(owner=user, patient=profile)
    SessionSummary.objects.create(session=session, text_summary="t", json_summary={}, tokens_used=1)
    response = api_client.get(f"/api/session/{session.id}/summary/")
    assert response.status_code == 200
    assert response.data["text_summary"] == "t"
