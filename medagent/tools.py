"""
LangChain tool definitions for the MedAgent agent.

These tools provide access to patient summaries, session summarization,
vision analysis, and profanity checking. They rely on the models and the
TakBot client to perform their work.
"""

import json
from medagent.models import PatientSummary, AccessHistory, SessionSummary, ChatMessage
from medagent.talkbot_client import tb_chat, vision_analyze, profanity


class GetPatientSummaryTool:
    def _run(self, patient_id: str) -> str:
        
        summary = PatientSummary.objects.get(patient_id=patient_id)
        return json.dumps(summary.json_data, ensure_ascii=False)


class SummarizeSessionTool:
    def _run(self, session_id: str) -> str:
        messages_qs = ChatMessage.objects.filter(session_id=session_id).order_by("created_at")
        if not messages_qs.exists():
            return "No messages to summarize"
        messages = [{"role": msg.role, "content": msg.content} for msg in messages_qs]
        result = tb_chat(messages, model="o3-mini")
        try:
            summary_data = json.loads(result)
            SessionSummary.objects.create(
                session_id=session_id,
                text_summary=summary_data.get("text_summary", ""),
                json_summary=summary_data,
                tokens_used=summary_data.get("token_count", 0)
            )
            return "Summary stored"
        except Exception:
            return "Invalid response from summarization service"


class ImageAnalysisTool:
    def _run(self, image_url: str) -> str:
        result = vision_analyze(image_url)
        return json.dumps(result, ensure_ascii=False)


class ProfanityCheckTool:
    def _run(self, text: str) -> str:
        result = profanity(text)
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except Exception:
                return "False"
        return str(result.get("contains_profanity", False))
