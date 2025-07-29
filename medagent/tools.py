"""
LangChain tool definitions for the MedAgent agent.

These tools provide access to patient summaries, session summarization,
vision analysis, and profanity checking. All tools are compatible with
LangChain v0.1.47+ and follow best practices for future-proofing.
"""

from __future__ import annotations

import json
from typing import Any

from langchain.tools import BaseTool
from medagent.models import PatientSummary, AccessHistory, ChatMessage, SessionSummary


# ---------------------- خلاصه وضعیت بیمار ----------------------
class GetPatientSummaryTool(BaseTool):
    name: str = "get_patient_summary"
    description: str = (
        "دریافت خلاصه بیمار با استفاده از user_id و patient_id (ورودی: dict). "
        "مقدار بازگشتی یک رشته‌ی JSON است که حاوی اطلاعات خلاصه‌ی وضعیت بیمار می‌باشد. "
        "در صورت عدم دسترسی، PermissionError پرتاب می‌شود."
    )

    def _run(self, tool_input: dict) -> str:
        # ورودی باید دیکشنری باشد
        if not isinstance(tool_input, dict):
            raise ValueError("tool_input باید dict باشد.")

        user_id = tool_input.get("user_id")
        patient_id = tool_input.get("patient_id")

        if not user_id or not patient_id:
            raise ValueError("user_id و patient_id باید ارائه شوند.")

        # الزام دسترسی (OTP تایید شده) -> تست انتظار PermissionError دارد
        has_access = AccessHistory.objects.filter(
            doctor_id=user_id, patient_id=patient_id
        ).exists()
        if not has_access:
            raise PermissionError("Access denied (OTP not verified)")

        try:
            summary = PatientSummary.objects.get(patient_id=patient_id)
            return json.dumps(summary.json_data, ensure_ascii=False)
        except PatientSummary.DoesNotExist:
            # مطابق نیاز: رشته پیام خطا برگردانده می‌شود
            return "خلاصه‌ای برای بیمار یافت نشد"

    def _arun(self, *args: Any, **kwargs: Any):
        raise NotImplementedError("async not supported")


# ---------------------- خلاصه‌سازی جلسه ----------------------
class SummarizeSessionTool(BaseTool):
    name: str = "summarize_session"
    description: str = (
        "خلاصه‌سازی مکالمات یک جلسه با استفاده از session_id (ورودی: str). "
        "خلاصه مکالمه را ایجاد و ذخیره می‌کند."
    )

    def _run(self, session_id: str) -> str:
        # import داخل متد تا monkeypatch در تست‌ها موثر باشد
        from medagent.talkbot_client import tb_chat

        # دریافت پیام‌ها
        messages_qs = ChatMessage.objects.filter(session_id=session_id).order_by("created_at")
        if not messages_qs.exists():
            return "هیچ پیامی برای خلاصه‌سازی یافت نشد"

        messages = [{"role": m.role, "content": m.content} for m in messages_qs]

        # تماس با مدل و parse نتیجه
        result = tb_chat(messages, model="o3-mini")
        try:
            summary_data = json.loads(result)
        except Exception:
            # اگر mock اعمال نشده باشد یا پاسخ نامعتبر باشد
            return "خطا در خلاصه‌سازی"

        # ذخیرهٔ خلاصه
        SessionSummary.objects.create(
            session_id=session_id,
            text_summary=summary_data.get("text_summary", ""),
            json_summary=summary_data,
            tokens_used=summary_data.get("token_count", 0),
        )
        return "خلاصه‌سازی انجام شد"

    def _arun(self, *args: Any, **kwargs: Any):
        raise NotImplementedError("async not supported")


# ---------------------- تحلیل تصویر ----------------------
class ImageAnalysisTool(BaseTool):
    name: str = "analyze_image"
    description: str = (
        "آپلود تصویر پزشکی (مسیر فایل) به مدل GPT-4 Vision / Gemini Vision و "
        "دریافت خروجی JSON تحلیل."
    )

    def _run(self, image_path: str, prompt: str | None = None) -> str:
        """
        image_path: مسیر فایل روی دیسک که باید Base64 شود.
        prompt: متنِ دلخواهِ کاربر برای مدل (optional).
        """
        from medagent.talkbot_client import vision_analyze

        # اگر کاربر پرامپت نداد، یک توضیح پیش‌فرض می‌فرستیم
        prompt = prompt or "Explain the medical findings in this image."

        result = vision_analyze(image_path=image_path, prompt=prompt)
        return json.dumps(result, ensure_ascii=False)

    @property
    def is_single_input(self) -> bool:  # pragma: no cover - override for agent
        return False

    def _arun(self, *args: Any, **kwargs: Any):
        raise NotImplementedError("async not supported")


# ---------------------- پالایش محتوا ----------------------
class ProfanityCheckTool(BaseTool):
    name: str = "check_profanity"
    description: str = (
        "بررسی وجود کلمات نامناسب در متن (ورودی: str). "
        "در صورت وجود profanity مقدار 'True' و در غیر این صورت 'False' به صورت رشته بازگردانده می‌شود."
    )

    def _run(self, text: str) -> str:
        # import داخل متد تا monkeypatch در تست‌ها موثر باشد
        from medagent.talkbot_client import profanity

        result = profanity(text)

        # پشتیبانی از هر دو خروجی ممکن: bool یا dict
        if isinstance(result, bool):
            return str(result)
        if isinstance(result, dict):
            return str(result.get("contains_profanity", False))

        # خروجی ناشناخته
        return "False"

    def _arun(self, *args: Any, **kwargs: Any):
        raise NotImplementedError("async not supported")
