from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import logging
from pathlib import Path
from typing import Any, Dict, List

import requests
from django.conf import settings

TALKBOT_BASE = settings.TALKBOT_API_BASE
TALKBOT_TOKEN = settings.TALKBOT_API_KEY
DEFAULT_MODEL = "gemini-pro-vision"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {TALKBOT_TOKEN}",
        "Content-Type": "application/json",
    }


# ---------- ابزار کمکی Base64 ---------- #

def encode_image_to_base64(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "application/octet-stream"
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def sha256_file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------- GPT-4 Vision / Gemini Vision ---------- #

def vision_analyze(
    image_path: str,
    prompt: str = "Explain the medical findings in this image.",
    model: str = DEFAULT_MODEL,
) -> dict:
    """ارسال تصویر (Base64) + متن به /v1/chat/completions و دریافت پاسخ تحلیلی."""
    try:
        if not Path(image_path).exists():
            raise FileNotFoundError(image_path)

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": encode_image_to_base64(image_path)},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "temperature": 0.7,
            "stream": False,
        }

        r = requests.post(
            f"{TALKBOT_BASE}/v1/chat/completions",
            headers=_headers(),
            json=payload,
            timeout=60,
        )
        r.raise_for_status()
        return r.json()

    except Exception as e:
        logging.exception("vision_analyze error")
        return {"error": "An error occurred during image analysis.", "label": "خطا", "finding": "نامشخص"}


# ---------- Profanity ---------- #

def profanity(text: str) -> dict:
    try:
        body = {"text": text}
        r = requests.post(
            f"{TALKBOT_BASE}/analysis/profanity/REQ",
            headers=_headers(),
            json=body,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, dict) else {"contains_profanity": False}
    except Exception:
        return {"contains_profanity": False}


# ---------- Chat (متن خالص) ---------- #

def tb_chat(messages: list[dict], model: str = "o3-mini") -> str:
    body = {"model": model, "messages": messages}
    try:
        r = requests.post(
            f"{TALKBOT_BASE}/chat",
            headers=_headers(),
            json=body,
            timeout=30,
        )
        r.raise_for_status()
        return r.text
    except Exception:
        return json.dumps({"text_summary": "خطا در ارتباط با مدل", "token_count": 0})
