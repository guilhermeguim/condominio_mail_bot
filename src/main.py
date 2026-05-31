"""Expose the webhook that validates, filters, and processes Telegram receipts.

This module is the orchestration layer of the application. It is responsible for
applying the fail-fast chat whitelist, validating that the update contains a
supported document, delegating the file download to the Telegram client,
delegating outbound delivery to the email service, and sending user-facing
status messages back to Telegram when the workflow reaches a known outcome.
"""

import os
import logging
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI

from src.email_service import send_email_with_attachment
from src.schemas import TelegramUpdateSchema
from src.telegram_client import get_telegram_file_bytes, send_message

load_dotenv()

app = FastAPI(title="Condominio Mail Bot")


@app.post("/webhook")
async def telegram_webhook(update: TelegramUpdateSchema) -> dict[str, str]:
    """Process a Telegram update and forward authorized PDF receipts by email.

    Args:
        update: Parsed Telegram payload containing the nested message/document
            structure used by the application, including the originating chat.

    Returns:
        A small status payload describing whether the update was ignored,
        silently acknowledged, or successfully forwarded.

    Raises:
        ValueError: If required runtime configuration is missing.
    """

    # Read the chat whitelist at request time so operational configuration can be changed without modifying source code.
    allowed_chat_ids_env = os.getenv("ALLOWED_CHAT_IDS")
    if not allowed_chat_ids_env:
        raise ValueError("The ALLOWED_CHAT_IDS environment variable is not set.")

    allowed_chat_ids = allowed_chat_ids_env.split(",")

    # Some Telegram updates do not include a standard message payload. The webhook ignores them early because there is no chat context to validate and no document to process.
    if not update.message or not update.message.chat:
        return {"status": "ignored", "reason": "Update does not contain a chat"}

    chat_id = str(update.message.chat.id)

    # Unauthorized chats are acknowledged with a successful response so Telegram does not retry the same request, while the application avoids spending any time downloading files or calling external services.
    if chat_id not in allowed_chat_ids:
        logging.warning("Blocked unauthorized chat: %s", chat_id)
        return {"status": "ok"}

    # After the chat is authorized, the next guardrail is message type: the bot only knows how to work with document uploads.
    if not update.message or not update.message.document:
        await send_message(int(chat_id), "Erro: A mensagem enviada não contém um documento.")
        return {"status": "ignored", "reason": "Update does not contain a document"}

    # The business rule for this workflow is intentionally narrow: only PDF documents are forwarded. Any other file type is rejected before download.
    if not update.message.document.mime_type or update.message.document.mime_type != "application/pdf":
        await send_message(int(chat_id), "Erro: O arquivo enviado não é um PDF válido.")
        return {"status": "ignored", "reason": "Document is not a PDF"}

    # Extract the minimal information needed by the downstream services.
    file_id = update.message.document.file_id
    file_name = update.message.document.file_name or "comprovante.pdf"

    # Download the file into memory first so the application can stay stateless and avoid temporary file management.
    file_bytes = await get_telegram_file_bytes(file_id)

    # Pass the same in-memory bytes directly to the email service so the file is attached and sent without any additional persistence step.
    await send_email_with_attachment(file_bytes, file_name)

    # Build the success message only after the email service completes without
    # raising an exception, so the chat feedback reflects the actual outcome.
    current_time = datetime.now().strftime("%H:%M")
    destination_email = os.getenv("DESTINATION_EMAIL")
    if not destination_email:
        raise ValueError("The DESTINATION_EMAIL environment variable is not set.")

    # The confirmation sent back to Telegram includes both the delivery time and the configured recipient so the user can verify where the receipt went.
    await send_message(int(chat_id), f"Sucesso! Comprovante encaminhado para a imobiliaria às {current_time}. Enviado para o endereço: {destination_email}")

    return {"status": "success", "message": "Email sent"}