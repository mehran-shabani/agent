"""
LangChain tool definitions for the MedAgent agent.

These tools provide access to patient summaries, session summarization,
vision analysis, and profanity checking. They rely on the models and the
TakBot client to perform their work.
"""

import json
from langchain.tools import BaseTool, Tool
from medagent.models import PatientSummary, AccessHistory, ChatMessage, SessionSummary
from medagent.talkbot_client import tb_chat, vision_analyze, profanity


# ---------------------- خلاصه بیمار ----------------------
def get_summary_tool_func(inputs: dict) -> str:
    """
    دریافت خلاصه وضعیت بیمار از طریق user_id و patient_id
    ورودی: dict با کلیدهای user_id و patient_id
    خروجی: str (JSON string)
    """
    user_id = inputs.get("user_id")
    patient_id = inputs.get("patient_id")

    if not user_id or not patient_id:
        return "user_id و patient_id باید ارائه شوند."

    if not AccessHistory.objects.filter(doctor_id=user_id, patient_id=patient_id).exists():
        return "دسترسی مجاز نیست (OTP تأیید نشده است)"

    try:
        summary = PatientSummary.objects.get(patient_id=patient_id)
        return json.dumps(summary.json_data, ensure_ascii=False)
    except PatientSummary.DoesNotExist:
        return "خلاصه‌ای برای بیمار یافت نشد"

# ابزار آماده برای LangChain
getpatientsummarytool = Tool(
    name: str = "get_patient_summary",
    func=get_summary_tool_func,
    is_single_input = True,
    description: str = "دریافت خلاصه بیمار با استفاده از user_id و patient_id (به صورت دیکشنری)"
)

# ---------------------- خلاصه جلسه ----------------------
class SummarizeSessionTool(BaseTool):
    name: str = "summarize_session"
    description: str = "خلاصه‌سازی مکالمات یک جلسه با استفاده از session_id"

    def _run(self, session_id: str) -> str:
        messages_qs = ChatMessage.objects.filter(session_id=session_id).order_by("created_at")
        if not messages_qs.exists():
            return "هیچ پیامی برای خلاصه‌سازی یافت نشد"

        messages = [{"role": m.role, "content": m.content} for m in messages_qs]
        result = tb_chat(messages, model="o3-mini")

        try:
            summary_data = json.loads(result)
        except Exception:
            return "خطا در خلاصه‌سازی"

        SessionSummary.objects.create(
            session_id=session_id,
            text_summary=summary_data.get("text_summary", ""),
            json_summary=summary_data,
            tokens_used=summary_data.get("token_count", 0)
        )
        return str("خلاصه‌سازی انجام شد")

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("async not supported")


# ---------------------- تحلیل تصویر ----------------------
class ImageAnalysisTool(BaseTool):
    name: str = "analyze_image"
    description: str = "تحلیل تصویر پزشکی از طریق URL"

    def _run(self, image_url: str) -> str:
        result = vision_analyze(image_url, input_type="url")
        return str(json.dumps(result, ensure_ascii=False))

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("async not supported")


# ---------------------- پالایش محتوا ----------------------
class ProfanityCheckTool(BaseTool):
    name: str = "check_profanity"
    description: str = "بررسی وجود کلمات نامناسب در متن"

    def _run(self, text: str) -> str:
        result = profanity(text)
        return str(result.get("contains_profanity", False))

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("async not supported")
