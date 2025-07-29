"""
Lightweight wrapper around the Kavenegar API for sending SMS messages.

In production, the KAVEHNEGAR_API_KEY should be stored in the environment.
For tests this module can be patched so that no network call is made.
"""
import os
from kavenegar import APIException, HTTPException, KavenegarAPI
from rest_framework import status
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

KAVEHNEGAR_API_KEY = os.getenv("KAVEHNEGAR_API_KEY")  # Should be stored in .env


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
    try:
          api = KavenegarAPI(KAVEHNEGAR_API_KEY)
          params = {
            'receptor': phone,
            'message': text,
            'template': 'otp_doctor'
            }
          api.verify_lookup(params)
    except (APIException, HTTPException) as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return False
    return True