import pytest
import json

@pytest.fixture(autouse=True)
def auto_mock_external(monkeypatch):
    """
    این fixture به‌صورت خودکار تمام توابع حساس و وابسته به API را mock می‌کند.
    فعال‌سازی آن در تمام تست‌ها به‌صورت global انجام می‌شود.
    """

    # Mock profanity check
    monkeypatch.setattr(
        "medagent.talkbot_client.profanity",
        lambda text: {"contains_profanity": False}
    )

    # Mock vision analysis
    monkeypatch.setattr(
        "medagent.talkbot_client.vision_analyze",
        lambda url, model="flux-ai": {"label": "X-ray", "finding": "normal"}
    )

    # Mock chat summarization
    monkeypatch.setattr(
        "medagent.talkbot_client.tb_chat",
        lambda messages, model="o3-mini": json.dumps({
            "text_summary": "mock summary",
            "chief_complaint": "mock complaint",
            "token_count": 42
        })
    )

    # Mock agent response (در صورت استفاده)
    monkeypatch.setattr(
        "medagent.agent_setup.agent.run",
        lambda msg: "mock assistant reply"
    )

    # Mock SMS sending
    monkeypatch.setattr(
        "medagent.sms.send_sms",
        lambda phone, text, sender=None: True
    )

    # ثابت‌سازی کد تصادفی OTP برای پیش‌بینی‌پذیری در تست‌ها
    import random
    monkeypatch.setattr(random, 'randint', lambda a, b: 123456)
