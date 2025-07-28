"""
Lightweight wrapper around the Kavenegar API for sending SMS messages.

In production, the KAVEHNEGAR_API_KEY should be stored in the environment.
For tests this module can be patched so that no network call is made.
"""

import os
import requests

KAVEHNEGAR_API_KEY = os.getenv("KAVEHNEGAR_API_KEY")  # Should be stored in .env
KAVEHNEGAR_URL = "https://api.kavenegar.com/v1/{api_key}/sms/send.json"

def send_sms(phone, text, sender=None):
    """
    Send an SMS via the Kavenegar API.

    :param phone: str, recipient phone number (e.g., 09121234567)
    :param text: str, message content
    :param sender: str, optional sender line
    :return: bool, True on success, False otherwise
    """
    if not KAVEHNEGAR_API_KEY:
        raise Exception("KAVEHNEGAR_API_KEY is not set.")

    url = KAVEHNEGAR_URL.format(api_key=KAVEHNEGAR_API_KEY)
    payload = {
        "receptor": phone,
        "message": text
    }
    if sender:
        payload["sender"] = sender

    try:
        res = requests.post(url, data=payload, timeout=10)
        res.raise_for_status()
        out = res.json()
        if out.get("return", {}).get("status") == 200:
            return True
        else:
            print("Kavenegar Error:", out)
            return False
    except Exception as e:
        print("Kavenegar SMS error:", e)
        return False
