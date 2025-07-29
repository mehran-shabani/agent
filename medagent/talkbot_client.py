"""
Client helpers to interact with the external TakBot API.

These functions wrap HTTP calls to the TakBot service for chat completions,
vision analysis and profanity detection. Authentication and request signing
are handled via environment variables. In tests these functions can be
patched to return deterministic results.
"""

import os
import json
import base64
import hashlib
import mimetypes
import requests
from django.conf import settings

TALKBOT_BASE = settings.TALKBOT_API_BASE
TALKBOT_TOKEN = settings.TALKBOT_API_KEY


def _headers(data: dict):
    return {
        "Authorization": TALKBOT_TOKEN,
        "Content-Type": "application/json",
        "Content-Length": str(len(json.dumps(data)))
    }


# ----------------------------- Profanity Check ----------------------------- #

def profanity(text: str) -> dict:
    """
    بررسی وجود کلمات نامناسب در متن.
    خروجی: {'contains_profanity': True/False}
    """
    body = {"text": text}
    try:
        r = requests.post(
            f"{TALKBOT_BASE}/analysis/profanity/REQ",
            headers=_headers(body),
            json=body,
            timeout=10
        )
        r.raise_for_status()
        result = r.json()
        return result if isinstance(result, dict) else {"contains_profanity": False}
    except Exception:
        return {"contains_profanity": False}


# ----------------------------- Image Encoding ----------------------------- #

def encode_image_to_base64(image_path: str) -> str:
    """
    تبدیل فایل تصویری به Base64 با فرمت data URI.
    """
    mime_type, _ = mimetypes.guess_type(image_path)
    mime_type = mime_type or "application/octet-stream"
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def sha256_file_hash(image_path: str) -> str:
    """
    محاسبه هش SHA256 فایل تصویر.
    """
    with open(image_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# --------------------------- Vision Analysis ----------------------------- #

def vision_analyze(image_input: str, model="flux-ai", input_type="url") -> dict:
    """
    تحلیل تصویر با مدل بینایی. ورودی می‌تواند URL یا Base64 باشد.

    :param image_input: مسیر فایل یا آدرس URL
    :param model: مدل انتخابی مثل flux-ai
    :param input_type: 'url' یا 'base64'
    :return: خروجی دیکشنری تحلیل
    """
    try:
        if input_type == "base64":
            data_uri = encode_image_to_base64(image_input)
            image_hash = sha256_file_hash(image_input)
            body = {"image_base64": data_uri, "image_hash": image_hash, "model": model}
        else:
            body = {"url": image_input, "model": model}

        r = requests.post(
            f"{TALKBOT_BASE}/analysis/vision",
            headers=_headers(body),
            json=body,
            timeout=20
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return {"label": "خطا", "finding": "نامشخص"}


# --------------------------- Chat Completion ----------------------------- #

def tb_chat(messages: list[dict], model="o3-mini") -> str:
    """
    دریافت خلاصه یا پاسخ هوشمند از مدل زبان.
    پیام‌ها باید لیستی از {"role": ..., "content": ...} باشند.
    """
    body = {"messages": messages, "model": model}
    try:
        r = requests.post(
            f"{TALKBOT_BASE}/chat",
            headers=_headers(body),
            json=body,
            timeout=30
        )
        r.raise_for_status()
        return r.text
    except Exception:
        return json.dumps({
            "text_summary": "خطا در ارتباط با مدل",
            "token_count": 0
        })
