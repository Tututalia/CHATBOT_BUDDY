"""
WhatsApp Webhook Server for Retail Agent (Twilio Integration).

Receives incoming WhatsApp messages via Twilio webhook, processes them through
the intelligent sales agent graph, and sends back responses (text + product images).
"""
import os
import sys
import json
import logging

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

# Ensure the backend package is importable (for intelligent_whatsapp_graph, crud, models, etc.)
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(os.path.join(BACKEND_DIR, ".env"))
logging.basicConfig(level=logging.INFO)

from intelligent_whatsapp_graph import (  # noqa: E402
    run_whatsapp_agent,
    send_whatsapp_text,
)

app = FastAPI(title="Retail Agent – WhatsApp Webhook")


# ─── Twilio Webhook (POST) ───────────────────────────────────────────

@app.post("/webhook")
async def webhook(request: Request):
    """
    Twilio sends incoming WhatsApp messages here as form-encoded POST.
    Fields of interest:
      - Body: the text message
      - From: sender in whatsapp:<E.164> format
      - To: your Twilio sandbox / business number
      - NumMedia, MediaUrl0, MediaContentType0, …  (for media messages)
    """
    form = await request.form()
    incoming_msg = (form.get("Body") or "").strip()
    # e.g. "whatsapp:+919876543210"
    sender = (form.get("From") or "").strip()
    num_media = int(form.get("NumMedia") or 0)

    logging.info(
        f"[Webhook] From={sender}  Body={incoming_msg!r}  NumMedia={num_media}")

    if not incoming_msg and num_media == 0:
        # Empty message — just acknowledge
        return _twiml_reply("Please send a text message so I can help you!")

    # If user sent an image/media without text, acknowledge
    if not incoming_msg and num_media > 0:
        return _twiml_reply("Thanks for the image! Please describe what you're looking for in text.")

    # ── Run the intelligent agent graph asynchronously ──
    try:
        # Strip the "whatsapp:" prefix to get a clean phone number for customer lookup
        clean_phone = sender.replace("whatsapp:", "")
        await run_whatsapp_agent(
            wa_id=clean_phone,
            message_body=incoming_msg,
            phone_number=clean_phone,
        )
    except Exception as exc:
        logging.exception(f"[Webhook] Agent error: {exc}")
        # Send a fallback error message via Twilio REST (outside TwiML)
        send_whatsapp_text(sender.replace(
            'whatsapp:', ''), "Sorry, something went wrong. Please try again in a moment.")

    # Return empty TwiML — we already sent replies via Twilio REST API
    return _twiml_empty()


# ─── Twilio Webhook Verification (GET) ───────────────────────────────

@app.get("/webhook")
async def webhook_verify():
    """
    Twilio doesn't require GET verification like Meta Cloud API,
    but we keep this endpoint alive for health-check / fallback.
    """
    return PlainTextResponse("Retail Agent WhatsApp Webhook is running.", status_code=200)


# ─── Health ──────────────────────────────────────────────────────────

@app.get("/")
def health():
    return {"status": "ok", "service": "Retail Agent WhatsApp Webhook"}


# ─── TwiML Helpers ───────────────────────────────────────────────────

def _twiml_reply(text: str) -> Response:
    """Return a TwiML response with a single text reply."""
    from twilio.twiml.messaging_response import MessagingResponse
    resp = MessagingResponse()
    resp.message(text)
    return Response(content=str(resp), media_type="application/xml")


def _twiml_empty() -> Response:
    """Return an empty TwiML response (we send messages via REST instead)."""
    from twilio.twiml.messaging_response import MessagingResponse
    resp = MessagingResponse()
    return Response(content=str(resp), media_type="application/xml")


# ─── Entry Point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
