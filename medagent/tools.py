"""
LangChain tool definitions for the MedAgent agent.

These tools provide access to patient summaries, session summarization,
vision analysis, and profanity checking. They rely on the models and the
TakBot client to perform their work.
"""

import json
from langchain.tools import BaseTool
from medagent.models import (
    PatientSummary, AccessHistory, ChatSession, SessionSummary
)
from talkbot_client import tb_chat, vision_analyze, profanity

class GetPatientSummaryTool(BaseTool):
    name = "get_patient_summary"
    description = "Retrieve the JSON patient summary if the doctor has access."

    def _run(self, doctor_id: str, patient_id: str) -> str:
        if not AccessHistory.objects.filter(doctor_id=doctor_id, patient_id=patient_id).exists():
            raise PermissionError("No access to patient")
        summary = PatientSummary.objects.get(patient_id=patient_id)
        return json.dumps(summary.json_data, ensure_ascii=False)

class SummarizeSessionTool(BaseTool):
    name = "summarize_session"
    description = "Summarize a chat session and store the result."

    def _run(self, session_id: str) -> str:
        sess = ChatSession.objects.prefetch_related("messages").get(id=session_id)
        history = "\n".join(f"{m.role}: {m.content}" for m in sess.messages.order_by("created_at"))
        prompt = (
            "خلاصهٔ ≤250 واژه + JSON دقیق با فیلدهای تعیین‌شده بساز.\n"
            "——\n" + history
        )
        response = tb_chat([{"role": "user", "content": prompt}])
        try:
            data = json.loads(response)
            text_summary = data.pop("text_summary")
            json_summary = data
            tokens_used = data.get("token_count", 0)
        except (json.JSONDecodeError, KeyError):
            # If the response is not valid JSON or missing expected keys, store the raw response
            text_summary = response
            json_summary = {}
            tokens_used = 0
        SessionSummary.objects.create(
            session=sess,
            text_summary=text_summary,
            json_summary=json_summary,
            tokens_used=tokens_used,
        )
        return "Summary stored"

class ImageAnalysisTool(BaseTool):
    name = "image_analysis"
    description = "Analyze an image and return a JSON object with findings."

    def _run(self, image_url: str) -> str:
        return json.dumps(vision_analyze(image_url), ensure_ascii=False)

class ProfanityCheckTool(BaseTool):
    name = "profanity_check"
    description = "Return 'True' if the text contains profanity."

    def _run(self, text: str) -> str:
        return str(profanity(text))
