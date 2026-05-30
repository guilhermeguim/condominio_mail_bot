"""Download Telegram files directly into memory for the email workflow.

The Telegram webhook only provides a ``file_id``. Turning that identifier into
raw bytes requires two API calls: one to resolve the internal ``file_path`` and
another to download the file contents from Telegram's file endpoint.
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_BASE_URL = "https://api.telegram.org"


async def get_telegram_file_bytes(file_id: str) -> bytes:
    """Resolve a Telegram ``file_id`` and return the downloaded file bytes.

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
    # The bot token is needed for both the metadata lookup and the binary file
    # download, so fail fast before opening any HTTP client.
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_bot_token:
        raise ValueError("The TELEGRAM_BOT_TOKEN environment variable is not set.")
    
    async with httpx.AsyncClient() as client:
        # The first call does not return the file itself. It only resolves the
        # ``file_id`` into the internal ``file_path`` used by Telegram's file CDN.
        response = await client.get(
            f"{TELEGRAM_API_BASE_URL}/bot{telegram_bot_token}/getFile",
            params={"file_id": file_id},
        )
        response.raise_for_status()

        # Telegram nests the actual metadata under ``result``. Using ``get``
        # with defaults avoids a KeyError and produces a clearer custom message.
        file_path = response.json().get("result", {}).get("file_path")
        if not file_path:
            raise ValueError("Telegram did not return a file path for the requested document.")
        
        # The second call targets Telegram's dedicated file endpoint and returns
        # the raw binary contents that will be forwarded by email.
        download_url = f"{TELEGRAM_API_BASE_URL}/file/bot{telegram_bot_token}/{file_path}"
        download_response = await client.get(download_url)
        download_response.raise_for_status()

        # Returning bytes keeps the caller free to decide whether to persist,
        # transform, or forward the file to another service.
        return download_response.content


        