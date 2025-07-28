import hashlib
import datetime

import pytest
from django.utils import timezone
from freezegun import freeze_time
from django.contrib.auth import get_user_model

from medagent.models import (
    PatientProfile, OTPVerification, ChatSession, ChatMessage,
    SessionSummary
)
from sub.models import SubscriptionPlan, Subscription

User = get_user_model()

@pytest.mark.django_db
def test_otp_verification_creation_and_validation():
    user = User.objects.create_user(username="testuser", password="pwd")
    profile = PatientProfile.objects.create(user=user, national_code="1234567890", phone_number="09120000000")
    raw_code = "123456"
    otp = OTPVerification.create(profile, raw_code)
    # Ensure the hash matches
    assert otp.code_hash == hashlib.sha256(raw_code.encode()).hexdigest()
    # Should be valid immediately after creation
    assert otp.valid(raw_code)
    # Invalid with wrong code
    assert not otp.valid("000000")
    # After expiration time, should not be valid
    future = timezone.now() + datetime.timedelta(minutes=11)
    with freeze_time(future):
        assert not otp.valid(raw_code)

@pytest.mark.django_db
def test_subscription_is_active_property():
    user = User.objects.create_user(username="subuser", password="pwd")
    plan = SubscriptionPlan.objects.create(name="Monthly", days=31, price=300)
    now = timezone.now()
    sub = Subscription.objects.create(user=user, plan=plan, end_date=now + datetime.timedelta(days=plan.days))
    # Immediately active
    assert sub.is_active
    # After expiry
    future = now + datetime.timedelta(days=plan.days + 1)
    with freeze_time(future):
        assert not sub.is_active

@pytest.mark.django_db
def test_chat_session_and_message_creation():
    user = User.objects.create_user(username="chatter", password="pwd")
    profile = PatientProfile.objects.create(user=user, national_code="0987654321", phone_number="09120000001")
    session = ChatSession.objects.create(owner=user, patient=profile)
    assert str(session).startswith("Session")
    msg_owner = ChatMessage.objects.create(session=session, role="owner", content="Hello")
    msg_assistant = ChatMessage.objects.create(session=session, role="assistant", content="Hi there")
    assert msg_owner.role == "owner"
    assert msg_assistant.role == "assistant"
    assert str(msg_owner).startswith("[owner]")

@pytest.mark.django_db
def test_session_summary_creation():
    user = User.objects.create_user(username="summarizer", password="pwd")
    profile = PatientProfile.objects.create(user=user, national_code="1111111111", phone_number="09120000002")
    session = ChatSession.objects.create(owner=user, patient=profile)
    ChatMessage.objects.create(session=session, role="owner", content="test")
    ChatMessage.objects.create(session=session, role="assistant", content="reply")
    summ = SessionSummary.objects.create(session=session, text_summary="A summary", json_summary={"key": "value"}, tokens_used=10)
    assert summ.session == session
    assert summ.text_summary == "A summary"
    assert summ.json_summary == {"key": "value"}
