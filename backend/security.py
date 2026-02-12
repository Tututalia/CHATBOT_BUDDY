from functools import wraps
from fastapi import Request, HTTPException
import logging
import hashlib
import hmac
from config import config


def validate_signature(payload, signature):
    """
    Validate the incoming payload's signature against our expected signature
    """
    # Use the App Secret to hash the payload
    expected_signature = hmac.new(
        bytes(config.APP_SECRET, "latin-1"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Check if the signature matches
    return hmac.compare_digest(expected_signature, signature)


def signature_required(f):
    """
    Decorator to ensure that the incoming requests to our webhook are valid and signed with the correct signature.
    """

    @wraps(f)
    async def decorated_function(request: Request, *args, **kwargs):
        signature_header = request.headers.get("X-Hub-Signature-256", "")
        logging.info(f"Signature header: {signature_header}")

        signature = signature_header[7:] if signature_header.startswith(
            "sha256=") else signature_header

        # Read body and store it in request.state for later use
        body = await request.body()
        body_str = body.decode("utf-8")

        # Log first 100 chars
        logging.info(f"Body received: {body_str[:100]}...")

        # Store the body in request state so the handler can access it
        request.state.body = body_str

        if not validate_signature(body_str, signature):
            logging.error(
                f"Signature verification failed! Signature: {signature}")
            raise HTTPException(
                status_code=403,
                detail="Invalid signature"
            )
        logging.info("Signature verified successfully")
        return await f(request, *args, **kwargs)

    return decorated_function
