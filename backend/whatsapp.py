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


# =====================================================================
# ============ Quick-Reply Buttons for WhatsApp =======================
# =====================================================================

# In-memory cache: context_name → Twilio Content SID
_CONTENT_TEMPLATE_CACHE: dict = {}

# Quick-reply button configurations for different conversation contexts.
# Each context has a body text and up to 3 action buttons (WhatsApp limit).
QUICK_ACTION_CONFIGS = {
    "main_menu": {
        "body": "⚡ Quick Actions:",
        "actions": [
            {"title": "🛒 View Cart", "id": "view_cart"},
            {"title": "🔍 Products", "id": "browse_products"},
            {"title": "📦 My Orders", "id": "my_orders"},
        ],
    },
    "after_recommendation": {
        "body": "What would you like to do?",
        "actions": [
            {"title": "🛒 Add to Cart", "id": "add_to_cart"},
            {"title": "👀 See More", "id": "see_more"},
            {"title": "🛒 View Cart", "id": "view_cart"},
        ],
    },
    "after_add_to_cart": {
        "body": "What's next?",
        "actions": [
            {"title": "🛒 View Cart", "id": "view_cart"},
            {"title": "🔍 Products", "id": "browse_products"},
            {"title": "💳 Checkout", "id": "checkout"},
        ],
    },
    "after_view_cart": {
        "body": "Choose an action:",
        "actions": [
            {"title": "💳 Checkout", "id": "checkout"},
            {"title": "🔍 Products", "id": "browse_products"},
            {"title": "❌ Remove Item", "id": "remove_item"},
        ],
    },
    "channel_select": {
        "body": "How would you like to buy?",
        "actions": [
            {"title": "🌐 Buy Online", "id": "buy_online"},
            {"title": "🏪 Store Pickup", "id": "store_pickup"},
        ],
    },
    "payment_methods": {
        "body": "Select payment method:",
        "actions": [
            {"title": "📱 UPI", "id": "upi"},
            {"title": "💳 Card", "id": "card"},
            {"title": "📦 Cash On Delivery", "id": "cash_on_delivery"},
        ],
    },
    "after_purchase": {
        "body": "Need anything else?",
        "actions": [
            {"title": "🔍 Products", "id": "browse_products"},
            {"title": "📦 My Orders", "id": "my_orders"},
            {"title": "⭐ Rate Us", "id": "rate_us"},
        ],
    },
    "cart_moved_online": {
        "body": "Your cart is ready! What would you like to do?",
        "actions": [
            {"title": "📋 Show Cart Items", "id": "show_cart_items"},
            {"title": "💳 Checkout", "id": "checkout"},
            {"title": "🔍 Products", "id": "browse_products"},
            {"title": "❌ Remove Item", "id": "remove_item"},
        ],
    },
}

# Mapping: button title text → natural-language command for the agent.
# When a user taps a quick-reply button, WhatsApp sends the button title as
# the message body, so we translate it to a full command the agent understands.
BUTTON_COMMAND_MAP = {
    "\ud83d\uded2 View Cart": "show me my cart",
    "\ud83d\udccb Show Cart Items": "show me my cart items",
    "\ud83d\udd0d Products": "show me products",
    "\ud83d\udce6 My Orders": "show me my order history",
    "🛒 Add to Cart": "I'd like to add the product to my cart",
    "👀 See More": "show me more products",
    "💳 Checkout": "I want to proceed to checkout",
    "❌ Remove Item": "I want to remove an item from my cart",
    "🌐 Buy Online": "I want to buy online",
    "🏪 Store Pickup": "I want to buy from nearest offline store",
    "📱 UPI": "I want to pay with UPI",
    "💳 Card": "I want to pay with credit card",
    "📦 Cash On Delivery": "I want to pay with cash on delivery",
    "⭐ Rate Us": "I want to leave feedback",
}


def _create_content_template(friendly_name: str, body: str, actions: list) -> str | None:
    """
    Create a Twilio Content Template (quick-reply) via the Content API.
    Returns the Content SID on success, or None on failure.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return None

    import requests as _req
    from requests.auth import HTTPBasicAuth

    url = "https://content.twilio.com/v1/Content"
    payload = {
        "friendly_name": friendly_name,
        "language": "en",
        "types": {
            "twilio/quick-reply": {
                "body": body,
                "actions": actions,
            }
        },
    }
    try:
        resp = _req.post(
            url, json=payload,
            auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            timeout=10,
        )
        if resp.status_code in (200, 201):
            sid = resp.json().get("sid")
            logging.info(
                f"[Twilio Content] Created template '{friendly_name}': {sid}")
            return sid
        else:
            logging.warning(
                f"[Twilio Content] Template creation failed ({resp.status_code}): "
                f"{resp.text[:200]}")
            return None
    except Exception as exc:
        logging.warning(
            f"[Twilio Content] Error creating template '{friendly_name}': {exc}")
        return None


def _get_content_sid(context: str) -> str | None:
    """Retrieve (or lazily create) the Twilio Content SID for a button context."""
    if context in _CONTENT_TEMPLATE_CACHE:
        return _CONTENT_TEMPLATE_CACHE[context]

    config = QUICK_ACTION_CONFIGS.get(context)
    if not config:
        return None

    friendly_name = f"retail_agent_wa_{context}"
    # WhatsApp quick-reply supports max 3 buttons; extra actions show in text fallback only
    sid = _create_content_template(
        friendly_name, config["body"], config["actions"][:3])
    if sid:
        _CONTENT_TEMPLATE_CACHE[context] = sid
    return sid


def send_quick_reply_buttons(to: str, context: str) -> bool:
    """
    Send a WhatsApp message with quick-reply buttons for the given context.

    Tries Twilio Content API first (actual clickable buttons in WhatsApp UI).
    Falls back to a formatted text menu if the Content API is unavailable.

    Args:
        to:      Recipient phone number (E.164 or ``whatsapp:`` prefix).
        context: One of the keys in ``QUICK_ACTION_CONFIGS``.

    Returns:
        True if buttons were sent successfully, False otherwise.
    """
    config = QUICK_ACTION_CONFIGS.get(context)
    if not config:
        return False

    # Normalise numbers (match _normalize_wa logic in intelligent_whatsapp_graph)
    to_num = to.strip()
    if not to_num.startswith("whatsapp:"):
        if not to_num.startswith("+"):
            to_num = f"whatsapp:+{to_num}"
        else:
            to_num = f"whatsapp:{to_num}"

    from_number = TWILIO_WHATSAPP_NUMBER.strip()
    if not from_number.startswith("whatsapp:"):
        from_number = f"whatsapp:{from_number}"

    # --- Primary: Twilio Content API (clickable buttons) ---
    content_sid = _get_content_sid(context)
    if content_sid:
        try:
            client = _get_twilio_client()
            msg = client.messages.create(
                content_sid=content_sid,
                from_=from_number,
                to=to_num,
            )
            logging.info(
                f"[Twilio] Quick-reply buttons sent ({context}): SID={msg.sid}")
            return True
        except Exception as exc:
            logging.warning(
                f"[Twilio] Content API send failed: {exc}")
            # Invalidate cached SID and fall through to text fallback
            _CONTENT_TEMPLATE_CACHE.pop(context, None)

    # --- Fallback: formatted text menu ---
    lines = [config["body"], ""]
    for i, action in enumerate(config["actions"], 1):
        lines.append(f"  {i}\ufe0f\u20e3  {action['title']}")
    lines.append("")
    lines.append("_Reply with an option above_")
    body = "\n".join(lines)

    try:
        client = _get_twilio_client()
        msg = client.messages.create(
            body=body, from_=from_number, to=to_num)
        logging.info(
            f"[Twilio] Text-menu fallback sent ({context}): SID={msg.sid}")
        return True
    except Exception as exc:
        logging.error(
            f"[Twilio] Failed to send text-menu fallback: {exc}")
        return False


def get_button_command(text: str) -> str | None:
    """
    Map a quick-action button title to the corresponding agent command.
    Returns ``None`` if the text is not a recognised button.
    """
    return BUTTON_COMMAND_MAP.get(text.strip())
