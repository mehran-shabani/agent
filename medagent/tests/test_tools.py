import json
import pytest
from django.contrib.auth import get_user_model
from medagent.models import PatientProfile, PatientSummary, AccessHistory, ChatSession, ChatMessage, SessionSummary
from medagent.tools import GetPatientSummaryTool, SummarizeSessionTool, ImageAnalysisTool, ProfanityCheckTool

User = get_user_model()

@pytest.mark.django_db
def test_get_patient_summary_tool_requires_access(monkeypatch):
    user = User.objects.create_user(username="doc", password="pwd")
    profile = PatientProfile.objects.create(user=user, national_code="3333333333", phone_number="09120000005")
    summary_data = {"height": 180}
    PatientSummary.objects.create(patient=profile, json_data=summary_data)
    tool = GetPatientSummaryTool()

    input_data = json.dumps({"user_id": str(user.id), "patient_id": str(profile.id)})

    # No access history yet -> should raise
    with pytest.raises(PermissionError):
        tool._run(input_data)

    # Grant access
    AccessHistory.objects.create(doctor=user, patient=profile)

    result = tool._run(input_data)
    assert json.loads(result) == summary_data

@pytest.mark.django_db
def test_summarize_session_tool_creates_summary(monkeypatch):
    # Patch tb_chat to return a JSON summary
    def fake_tb_chat(messages, model="o3-mini"):
        return json.dumps({
            "text_summary": "short summary",
            "chief_complaint": "headache",
            "token_count": 50
        })
    monkeypatch.setattr("medagent.talkbot_client.tb_chat", fake_tb_chat)
    user = User.objects.create_user(username="sumdoc", password="pwd")
    profile = PatientProfile.objects.create(user=user, national_code="4444444444", phone_number="09120000006")
    session = ChatSession.objects.create(owner=user, patient=profile)
    # Populate some messages
    ChatMessage.objects.create(session=session, role="owner", content="hi")
    ChatMessage.objects.create(session=session, role="assistant", content="hello")
    tool = SummarizeSessionTool()
    result = tool._run(str(session.id))
    assert result == "Summary stored"
    summary = SessionSummary.objects.get(session=session)
    assert summary.text_summary == "short summary"
    assert summary.json_summary.get("chief_complaint") == "headache"
    assert summary.tokens_used == 50

@pytest.mark.django_db
def test_image_analysis_tool(monkeypatch):
    # Patch vision_analyze to return predetermined dict
    def fake_vision(url, model="flux-ai"):
        return {"label": "X-ray", "finding": "normal"}
    monkeypatch.setattr("medagent.talkbot_client.vision_analyze", fake_vision)
    tool = ImageAnalysisTool()
    result = tool._run("http://example.com/image.png")
    assert json.loads(result) == {"label": "X-ray", "finding": "normal"}

def test_profanity_check_tool(monkeypatch):
    # Patch profanity to return True/False values
    monkeypatch.setattr("medagent.talkbot_client.profanity", lambda text: True)
    tool = ProfanityCheckTool()
    assert tool._run("bad words") == "True"
    monkeypatch.setattr("medagent.talkbot_client.profanity", lambda text: False)
    assert tool._run("good words") == "False"
