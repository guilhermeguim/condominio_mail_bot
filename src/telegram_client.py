"""Interact with Telegram's Bot API for downloads and chat feedback.

This module serves both Telegram-facing responsibilities used by the webhook:
resolving a ``file_id`` into raw file bytes and sending a plain-text reply back
to the originating chat. Keeping both operations together avoids duplicating the
bot token handling and HTTP client setup conventions.
"""

import os
import logging

import httpx
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_BASE_URL = "https://api.telegram.org"


async def get_telegram_file_bytes(file_id: str) -> bytes:
    """Resolve a Telegram ``file_id`` and download the corresponding bytes.

    Args:
        file_id: Telegram's opaque identifier for the document attached to the
            inbound message.

    Returns:
        The raw bytes downloaded from Telegram's file API.

    Raises:
        ValueError: If the bot token is missing or Telegram does not return a
            usable ``file_path``.
        httpx.HTTPStatusError: If either Telegram API request fails.
    """
    # The bot token is needed for both the metadata lookup and the binary file download, so fail fast before opening any HTTP client.
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_bot_token:
        raise ValueError("The TELEGRAM_BOT_TOKEN environment variable is not set.")
    
    async with httpx.AsyncClient() as client:
        # The first call does not return the file itself. It only resolves the ``file_id`` into the internal ``file_path`` used by Telegram's file CDN.
        response = await client.get(
            f"{TELEGRAM_API_BASE_URL}/bot{telegram_bot_token}/getFile",
            params={"file_id": file_id},
        )
        response.raise_for_status()

        # Telegram nests the actual metadata under ``result``. Using ``get`` with defaults avoids a KeyError and produces a clearer custom message.
        file_path = response.json().get("result", {}).get("file_path")
        if not file_path:
            raise ValueError("Telegram did not return a file path for the requested document.")
        
        # The second call targets Telegram's dedicated file endpoint and returns the raw binary contents that will be forwarded by email.
        download_url = f"{TELEGRAM_API_BASE_URL}/file/bot{telegram_bot_token}/{file_path}"
        download_response = await client.get(download_url)
        download_response.raise_for_status()

        # Returning bytes keeps the caller free to decide whether to persist, transform, or forward the file to another service.
        return download_response.content


async def send_message(chat_id: int, text: str) -> bool:
    """Send a plain-text feedback message to a Telegram chat.

    Args:
        chat_id: The numerical identifier of the target conversation.
        text: The message body that should be shown to the user in Telegram.

    Returns:
        ``True`` when Telegram accepts the outbound message and ``False`` when a
        transport or API error prevents the reply from being sent.

    Raises:
        ValueError: If the bot token is missing from the environment.
    """
    # The bot token is required for authorization. Check it before attempting network I/O so configuration errors fail fast and clearly.
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_bot_token:
        raise ValueError("The TELEGRAM_BOT_TOKEN environment variable is not set.")

    send_message_url = f"{TELEGRAM_API_BASE_URL}/bot{telegram_bot_token}/sendMessage"
    message_payload = {"chat_id": chat_id, "text": text}

    try:
        async with httpx.AsyncClient() as client:
            # Telegram expects a JSON payload containing both the destination chat identifier and the text that should be rendered to the user.
            response = await client.post(send_message_url, json=message_payload)
            response.raise_for_status()

            # Returning True allows the caller to know the delivery succeeded.
            return True

    except httpx.HTTPError as exc:
        # Feedback delivery should never crash the whole webhook flow, so the error is logged and the caller receives a simple failure signal.
        logging.error("Failed to send Telegram message: %s", exc)
        return False