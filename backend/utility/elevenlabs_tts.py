"""
ElevenLabs Text-to-Speech Utility for Retail Agent Chatbot
===========================================================

Converts LLM response text to speech using the ElevenLabs API.
Voice selection is gender-opposite to the customer:
  - Male customer   → Female voice
  - Female customer  → Male voice

Usage (standalone):
    python elevenlabs_tts.py --customer_id CUS001 --text "Hello, welcome!"
    python elevenlabs_tts.py --customer_id CUS001 --text "Hello!" --play

Usage (as module):
    from utility.elevenlabs_tts import generate_speech, generate_speech_for_customer

    # Direct: pass gender explicitly
    audio_bytes = generate_speech("Welcome!", customer_gender="Male")

    # Auto-lookup: fetch gender from DB using customer_id
    audio_bytes = generate_speech_for_customer("CUS001", "Welcome!")
"""

import os
import sys
import io
import argparse
import requests
from typing import Optional
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Resolve project paths so this script works both as a standalone utility
# and when imported from the backend package.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_SCRIPT_DIR)

if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

load_dotenv(os.path.join(_BACKEND_DIR, ".env"))

# ---------------------------------------------------------------------------
# ElevenLabs Configuration
# ---------------------------------------------------------------------------
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

# Pre-configured voice IDs (ElevenLabs default voices)
# You can replace these with any voice_id from your ElevenLabs account.
VOICE_MAP = {
    # Female voice – used when customer is Male
    "female": {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",   # "Sarah" – warm, friendly female
        "name": "Sarah",
    },
    # Male voice – used when customer is Female
    "male": {
        "voice_id": "TX3LPaxmHKxFdv7VOQHJ",    # "Liam" – confident, clear male
        "name": "Liam",
    },
}

# Default TTS settings
# eleven_turbo_v2_5 is optimized for LOW LATENCY (~50% faster than v2)
# Still supports multilingual (English, Hindi, Bengali & more)
DEFAULT_MODEL_ID = "eleven_turbo_v2_5"
DEFAULT_STABILITY = 0.5
DEFAULT_SIMILARITY_BOOST = 0.75
DEFAULT_STYLE = 0.0
# mp3_22050_32 is ~4x smaller than mp3_44100_128 → much faster transfer
# Still good quality for voice playback in a chatbot
DEFAULT_OUTPUT_FORMAT = "mp3_22050_32"
# Streaming latency optimization level (0-4)
# 4 = maximum latency optimization (may slightly reduce quality)
DEFAULT_OPTIMIZE_STREAMING_LATENCY = 4

# Reusable HTTP session for connection pooling (avoids TLS handshake per request)
_http_session = requests.Session()


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def _select_voice(customer_gender: str) -> dict:
    """
    Select the opposite-gender voice based on the customer's gender.

    Args:
        customer_gender: The customer's gender ("Male", "Female", etc.)

    Returns:
        Dict with 'voice_id' and 'name' keys.
    """
    gender_lower = (customer_gender or "").strip().lower()

    if gender_lower in ("male", "m"):
        # Male customer → Female AI voice
        return VOICE_MAP["female"]
    elif gender_lower in ("female", "f"):
        # Female customer → Male AI voice
        return VOICE_MAP["male"]
    else:
        # Default to female voice for unknown/unspecified genders
        return VOICE_MAP["female"]


def generate_speech(
    text: str,
    customer_gender: str = "male",
    model_id: str = DEFAULT_MODEL_ID,
    stability: float = DEFAULT_STABILITY,
    similarity_boost: float = DEFAULT_SIMILARITY_BOOST,
    style: float = DEFAULT_STYLE,
    output_format: str = DEFAULT_OUTPUT_FORMAT,
    api_key: Optional[str] = None,
) -> bytes:
    """
    Convert text to speech using the ElevenLabs API.

    Args:
        text:              The text to convert to speech.
        customer_gender:   Gender of the customer ("Male" / "Female").
                           The AI voice will be the opposite gender.
        model_id:          ElevenLabs model to use.
        stability:         Voice stability (0.0 – 1.0).
        similarity_boost:  Voice similarity boost (0.0 – 1.0).
        style:             Style exaggeration (0.0 – 1.0).
        output_format:     Audio output format (e.g. "mp3_44100_128").
        api_key:           Optional API key override.

    Returns:
        Raw audio bytes (MP3 by default).

    Raises:
        ValueError:  If text is empty.
        RuntimeError: If the ElevenLabs API returns an error.
    """
    if not text or not text.strip():
        raise ValueError("Text must not be empty.")

    key = api_key or ELEVENLABS_API_KEY
    if not key:
        raise RuntimeError(
            "ElevenLabs API key is not set. "
            "Set ELEVENLABS_API_KEY in your .env file or pass it explicitly."
        )

    voice = _select_voice(customer_gender)
    voice_id = voice["voice_id"]
    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    payload = {
        "text": text.strip(),
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": True,
        },
    }

    # Add output format and latency optimization as query params
    params = {
        "output_format": output_format,
        "optimize_streaming_latency": DEFAULT_OPTIMIZE_STREAMING_LATENCY,
    }

    response = _http_session.post(
        url, json=payload, headers=headers, params=params, timeout=30)

    if response.status_code != 200:
        error_detail = response.text[:500]
        raise RuntimeError(
            f"ElevenLabs API error (HTTP {response.status_code}): {error_detail}"
        )

    return response.content


def generate_speech_stream(
    text: str,
    customer_gender: str = "male",
    model_id: str = DEFAULT_MODEL_ID,
    stability: float = DEFAULT_STABILITY,
    similarity_boost: float = DEFAULT_SIMILARITY_BOOST,
    style: float = DEFAULT_STYLE,
    output_format: str = DEFAULT_OUTPUT_FORMAT,
    api_key: Optional[str] = None,
):
    """
    Stream audio chunks from ElevenLabs API for real-time playback.
    Uses the /stream endpoint so audio starts playing almost immediately
    instead of waiting for the entire file to be generated.

    This significantly reduces time-to-first-audio from ~2-5s to ~200-500ms.

    Args:
        text:              The text to convert to speech.
        customer_gender:   Gender of the customer ("Male" / "Female").
        model_id:          ElevenLabs model to use.
        stability:         Voice stability (0.0 – 1.0).
        similarity_boost:  Voice similarity boost (0.0 – 1.0).
        style:             Style exaggeration (0.0 – 1.0).
        output_format:     Audio output format.
        api_key:           Optional API key override.

    Yields:
        bytes: Audio chunks (MP3 fragments) as they arrive from the API.
    """
    if not text or not text.strip():
        raise ValueError("Text must not be empty.")

    key = api_key or ELEVENLABS_API_KEY
    if not key:
        raise RuntimeError(
            "ElevenLabs API key is not set. "
            "Set ELEVENLABS_API_KEY in your .env file or pass it explicitly."
        )

    voice = _select_voice(customer_gender)
    voice_id = voice["voice_id"]
    # Use the /stream endpoint for chunked transfer
    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}/stream"

    headers = {
        "xi-api-key": key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    payload = {
        "text": text.strip(),
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": True,
        },
    }

    params = {
        "output_format": output_format,
        "optimize_streaming_latency": DEFAULT_OPTIMIZE_STREAMING_LATENCY,
    }

    with _http_session.post(
        url, json=payload, headers=headers, params=params, timeout=30, stream=True
    ) as response:
        if response.status_code != 200:
            error_detail = response.text[:500]
            raise RuntimeError(
                f"ElevenLabs API error (HTTP {response.status_code}): {error_detail}"
            )
        # 512-byte chunks → first audio arrives faster than 1024
        for chunk in response.iter_content(chunk_size=512):
            if chunk:
                yield chunk


def generate_speech_stream_for_customer(
    customer_id: str,
    text: str,
    **kwargs,
):
    """
    High-level streaming helper: fetches customer gender from DB,
    then streams gender-opposite TTS audio chunks.

    Args:
        customer_id: The customer ID to look up.
        text:        The LLM response text to convert to speech.
        **kwargs:    Additional keyword args forwarded to generate_speech_stream().

    Yields:
        bytes: Audio chunks (MP3 fragments).
    """
    gender = get_customer_gender_from_db(customer_id)
    voice = _select_voice(gender)
    print(
        f"[ElevenLabs TTS] Streaming — Customer {customer_id} (gender={gender}) "
        f"→ Using {voice['name']} voice ({voice['voice_id']})"
    )
    yield from generate_speech_stream(text, customer_gender=gender, **kwargs)


def get_customer_gender_from_db(customer_id: str) -> str:
    """
    Look up the customer's gender from the SQLite database.

    Args:
        customer_id: The customer ID (e.g. "CUS001").

    Returns:
        Gender string (e.g. "Male", "Female") or "unknown".
    """
    try:
        from database import engine
        from models import Customer
        from sqlmodel import Session, select

        with Session(engine) as session:
            statement = select(Customer).where(
                Customer.customer_id == customer_id)
            customer = session.exec(statement).first()
            if customer and customer.gender:
                return customer.gender
    except Exception as e:
        print(
            f"[ElevenLabs TTS] Warning: Could not fetch customer gender: {e}")

    return "unknown"


def generate_speech_for_customer(
    customer_id: str,
    text: str,
    **kwargs,
) -> bytes:
    """
    High-level helper: fetches the customer's gender from the DB,
    then generates gender-opposite TTS audio.

    Args:
        customer_id: The customer ID to look up.
        text:        The LLM response text to convert to speech.
        **kwargs:    Additional keyword args forwarded to generate_speech().

    Returns:
        Raw audio bytes (MP3).
    """
    gender = get_customer_gender_from_db(customer_id)
    voice = _select_voice(gender)
    print(
        f"[ElevenLabs TTS] Customer {customer_id} (gender={gender}) "
        f"→ Using {voice['name']} voice ({voice['voice_id']})"
    )
    return generate_speech(text, customer_gender=gender, **kwargs)


def save_audio_to_file(audio_bytes: bytes, filepath: str) -> str:
    """
    Save raw audio bytes to a file.

    Args:
        audio_bytes: The audio content.
        filepath:    Destination file path.

    Returns:
        Absolute path of the saved file.
    """
    abs_path = os.path.abspath(filepath)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(audio_bytes)
    print(f"[ElevenLabs TTS] Audio saved to: {abs_path}")
    return abs_path


def audio_to_base64(audio_bytes: bytes) -> str:
    """
    Encode audio bytes to a base64 string (useful for sending via JSON/WebSocket).

    Args:
        audio_bytes: Raw audio content.

    Returns:
        Base64-encoded string.
    """
    import base64
    return base64.b64encode(audio_bytes).decode("utf-8")


# ---------------------------------------------------------------------------
# FastAPI Endpoint Helper
# ---------------------------------------------------------------------------

def create_tts_endpoint_handler():
    """
    Returns an async handler function that can be registered as a FastAPI endpoint.
    Supports both streaming (default) and non-streaming modes.

    Streaming mode uses chunked transfer so the browser starts playing audio
    within ~200-500ms instead of waiting 2-5s for the full file.

    Example usage in main.py:
        from utility.elevenlabs_tts import create_tts_endpoint_handler
        app.post("/api/elevenlabs-tts")(create_tts_endpoint_handler())
    """
    from fastapi.responses import Response, StreamingResponse, JSONResponse
    from pydantic import BaseModel

    class ElevenLabsTTSRequest(BaseModel):
        text: str
        customer_id: str | None = None
        customer_gender: str | None = None  # "Male" or "Female"
        stream: bool = True  # Streaming enabled by default for low latency

    async def elevenlabs_tts_handler(request: ElevenLabsTTSRequest):
        """
        POST /api/elevenlabs-tts
        Body: { "text": "...", "customer_id": "CUS001" }
           or { "text": "...", "customer_gender": "Male", "stream": true }

        Returns: audio/mpeg — streamed in chunks (default) or as a full response.
        """
        # Determine gender
        gender = request.customer_gender
        if not gender and request.customer_id:
            gender = get_customer_gender_from_db(request.customer_id)
        if not gender:
            gender = "unknown"

        voice = _select_voice(gender)
        print(
            f"[ElevenLabs TTS] Request — gender={gender} "
            f"→ voice={voice['name']} ({voice['voice_id']}) "
            f"streaming={request.stream}"
        )

        response_headers = {
            "Content-Disposition": "inline; filename=tts_response.mp3",
            "X-Voice-Name": voice["name"],
            "X-Customer-Gender": gender,
        }

        try:
            if request.stream:
                # Streaming: audio chunks sent as they arrive from ElevenLabs
                # Time-to-first-audio: ~200-500ms instead of 2-5s
                return StreamingResponse(
                    generate_speech_stream(
                        text=request.text,
                        customer_gender=gender,
                    ),
                    media_type="audio/mpeg",
                    headers=response_headers,
                )
            else:
                # Non-streaming: full audio returned at once
                audio_bytes = generate_speech(
                    text=request.text,
                    customer_gender=gender,
                )
                return Response(
                    content=audio_bytes,
                    media_type="audio/mpeg",
                    headers=response_headers,
                )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": str(e)},
            )

    return elevenlabs_tts_handler


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ElevenLabs TTS — Generate speech from text with gender-opposite voice."
    )
    parser.add_argument("--text", "-t", required=True,
                        help="Text to convert to speech.")
    parser.add_argument("--customer_id", "-c", default=None,
                        help="Customer ID to look up gender from DB.")
    parser.add_argument("--gender", "-g", default=None,
                        help="Explicit customer gender (Male/Female). Overrides DB lookup.")
    parser.add_argument("--output", "-o", default="tts_output.mp3",
                        help="Output file path (default: tts_output.mp3).")
    parser.add_argument("--play", action="store_true",
                        help="Play audio after generation (requires system audio player).")

    args = parser.parse_args()

    # Determine gender
    gender = args.gender
    if not gender and args.customer_id:
        gender = get_customer_gender_from_db(args.customer_id)
        print(f"[ElevenLabs TTS] Looked up gender from DB: {gender}")
    elif not gender:
        gender = "unknown"
        print("[ElevenLabs TTS] No gender specified, using default female voice.")

    voice = _select_voice(gender)
    print(
        f"[ElevenLabs TTS] Customer gender: {gender} → AI voice: {voice['name']}")

    # Generate speech
    print(
        f"[ElevenLabs TTS] Generating speech for: \"{args.text[:80]}{'...' if len(args.text) > 80 else ''}\"")
    audio_bytes = generate_speech(text=args.text, customer_gender=gender)
    print(f"[ElevenLabs TTS] Received {len(audio_bytes):,} bytes of audio.")

    # Save to file
    save_audio_to_file(audio_bytes, args.output)

    # Optionally play
    if args.play:
        import platform
        system = platform.system()
        abs_path = os.path.abspath(args.output)
        print(f"[ElevenLabs TTS] Playing audio...")
        if system == "Windows":
            os.system(f'start "" "{abs_path}"')
        elif system == "Darwin":
            os.system(f'afplay "{abs_path}"')
        else:
            os.system(
                f'xdg-open "{abs_path}" 2>/dev/null || aplay "{abs_path}"')


if __name__ == "__main__":
    main()
