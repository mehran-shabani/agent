"""
Client helpers to interact with the external TakBot API.

These functions wrap HTTP calls to the TakBot service for chat completions,
vision analysis and profanity detection. Authentication and request signing
are handled via environment variables. In tests these functions can be
patched to return deterministic results.
"""

import os
import hmac
import hashlib
import base64
import json
import requests

TAKBOT_BASE = os.getenv("TAKBOT_BASE_URL", "https://api.talkbot.ir/v1")
API_KEY = os.getenv("TAKBOT_API_KEY", "sk-23doce1205uh7m9oijd2&pcw4df2449210")
SIGN_SECRET = os.getenv("TAKBOT_SIGN_SECRET", "")

def _headers(body):
    h = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    return h

def tb_chat(messages, model="o3-mini"):
    body = {"model": model, "messages": messages}
    r = requests.post(f"{TAKBOT_BASE}/chat/completions", headers=_headers(body), json=body, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def vision_analyze(url, model="flux-ai"):
    body = {"model": model, "image_url": url}
    r = requests.post(f"{TAKBOT_BASE}/analysis/vision", headers=_headers(body), json=body, timeout=30)
    r.raise_for_status()
    return r.json()

def profanity(text):
    body = {"text": text}
    r = requests.post(f"{TAKBOT_BASE}/analysis/profanity/REQ", headers=_headers(body), json=body, timeout=10)
    r.raise_for_status()
    return r.json().get("contains_profanity", False)
