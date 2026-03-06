"""
WhatsApp integration via Twilio for the Retail Agent.
Sends text messages and media (product images) through Twilio's WhatsApp API.
"""
import os
import logging
import re
from dotenv import load_dotenv

load_dotenv()

# Twilio credentials – set these in your .env
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv(
    "TWILIO_WHATSAPP_NUMBER", "")  # e.g. "whatsapp:+14155238886"

# Public base URL where product images are accessible.
PRODUCT_IMAGE_BASE_URL = os.getenv("PRODUCT_IMAGE_BASE_URL", "")


def _get_twilio_client():
    """Lazy-init a Twilio REST client."""
    from twilio.rest import Client
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def _normalize_whatsapp_number(number: str) -> str:
    """Ensure the number is in whatsapp:<E.164> format."""
    number = number.strip()
    if not number.startswith("whatsapp:"):
        number = f"whatsapp:{number}"
    return number


def send_text_message(to: str, body: str):
    """
    Send a plain text WhatsApp message via Twilio.

    Args:
        to: Recipient phone in E.164 format (e.g. "+919876543210") or "whatsapp:+919876543210"
        body: The text body.
    """
    client = _get_twilio_client()
    to = _normalize_whatsapp_number(to)
    from_number = _normalize_whatsapp_number(TWILIO_WHATSAPP_NUMBER)

    try:
        chunks = _split_text(body, max_len=1500)
        for chunk in chunks:
            msg = client.messages.create(
                body=chunk,
                from_=from_number,
                to=to,
            )
            logging.info(f"[Twilio] Text sent to {to}: SID={msg.sid}")
    except Exception as exc:
        logging.error(f"[Twilio] Failed to send text to {to}: {exc}")


def send_image_message(to: str, image_url: str, caption: str = ""):
    """
    Send an image (media) WhatsApp message via Twilio.

    Args:
        to: Recipient phone in E.164 format or "whatsapp:..." format.
        image_url: Publicly accessible URL of the image.
        caption: Optional caption text for the image.
    """
    client = _get_twilio_client()
    to = _normalize_whatsapp_number(to)
    from_number = _normalize_whatsapp_number(TWILIO_WHATSAPP_NUMBER)

    try:
        msg = client.messages.create(
            body=caption[:1600] if caption else "",
            from_=from_number,
            to=to,
            media_url=[image_url],
        )
        logging.info(f"[Twilio] Image sent to {to}: SID={msg.sid}")
    except Exception as exc:
        logging.error(f"[Twilio] Failed to send image to {to}: {exc}")


def resolve_image_url(image_reference: str | None) -> str | None:
    """Convert a relative /images/PRDxxx.jpg path to a fully-qualified public URL."""
    if not image_reference:
        return None
    if image_reference.startswith("http"):
        return image_reference
    path = image_reference.lstrip("/")
    base = PRODUCT_IMAGE_BASE_URL.rstrip("/")
    if not base:
        return None
    return f"{base}/{path}"


def _split_text(text: str, max_len: int = 1500) -> list:
    """Split long text into chunks that fit within Twilio's recommended limit."""
    if not text:
        return [""]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        idx = text.rfind("\n", 0, max_len)
        if idx == -1:
            idx = max_len
        chunks.append(text[:idx])
        text = text[idx:].lstrip("\n")
    return chunks


def process_text_for_whatsapp(text):
    """Convert markdown-style bold to WhatsApp-style bold."""
    pattern = r"\【.*?\】"
    text = re.sub(pattern, "", text).strip()
    pattern = r"\*\*(.*?)\*\*"
    replacement = r"*\1*"
    whatsapp_style_text = re.sub(pattern, replacement, text)
    return whatsapp_style_text


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )


# ---- Legacy aliases for backward compatibility ----
def send_message(data):
    """Legacy Meta Cloud API send_message — now a no-op stub."""
    logging.warning(
        "[whatsapp] send_message (Meta Cloud API) called but deprecated. Use send_text_message instead.")


def get_text_message_input(recipient, text):
    """Legacy Meta Cloud API helper — now a no-op stub."""
    logging.warning(
        "[whatsapp] get_text_message_input (Meta Cloud API) called but deprecated.")
    import json
    return json.dumps({"to": recipient, "text": text})
