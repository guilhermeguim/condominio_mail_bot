"""Expose the FastAPI webhook that connects Telegram downloads to email delivery.

The application entrypoint stays intentionally small. Its job is to validate the
incoming Telegram payload, reject unsupported updates early, and orchestrate the
two integration services responsible for downloading the file and sending the
email.
"""

from fastapi import FastAPI
from dotenv import load_dotenv

from src.email_service import send_email_with_attachment
from src.schemas import TelegramUpdateSchema
from src.telegram_client import get_telegram_file_bytes
import os
import logging
from datetime import datetime
from src.telegram_client import get_telegram_file_bytes, send_message

load_dotenv()

app = FastAPI(title="Condominio Mail Bot")


@app.post("/webhook")
async def telegram_webhook(update: TelegramUpdateSchema) -> dict[str, str]:
    """Handle a Telegram webhook update and forward supported documents by email.

    Args:
        update: Parsed Telegram payload containing the nested message/document
            structure used by the application.

    Returns:
        A small status payload describing whether the update was ignored or
        successfully forwarded.
    """
    
    allowed_chat_ids_env = os.getenv("ALLOWED_CHAT_IDS")
    if not allowed_chat_ids_env:
        raise ValueError("The ALLOWED_CHAT_IDS environment variable is not set.")
    
    allowed_chat_ids = allowed_chat_ids_env.split(",")
    
    if not update.message or not update.message.chat:
        return {"status": "ignored", "reason": "Update does not contain a chat"}
    
    chat_id = str(update.message.chat.id)
    

    if chat_id not in allowed_chat_ids:
        logging.warning(f"Bloqueio de chat não autorizado: {chat_id}")
        return {"status": "ok"}
    
    # Telegram can send many event types. This automation only cares aboutupdates that carry a document inside the message payload.
    if not update.message or not update.message.document:
        await send_message(int(chat_id), "Erro: A mensagem enviada não contém um documento.")
        return {"status": "ignored", "reason": "Update does not contain a document"}
    
    # The current business rule only accepts PDF files. Rejecting early keeps the download and email services from running for unsupported attachments.
    if not update.message.document.mime_type or update.message.document.mime_type != "application/pdf":
        await send_message(int(chat_id), "Erro: O arquivo enviado não é um PDF válido.")
        return {"status": "ignored", "reason": "Document is not a PDF"}
    
    # Extract the minimal information needed by the downstream services.
    file_id = update.message.document.file_id
    file_name = update.message.document.file_name or "comprovante.pdf"
    
    # Download the file into memory first; the service returns raw bytes rather than a temporary path so the workflow never depends on local disk writes.
    file_bytes = await get_telegram_file_bytes(file_id)

    # Pass the same in-memory bytes directly to the email service so the file is attached and sent without any additional persistence step.
    await send_email_with_attachment(file_bytes, file_name)
    
    # MENSAGEM DE SUCESSO PARA O USUÁRIO
    current_time = datetime.now().strftime("%H:%M")
    destination_email = os.getenv("DESTINATION_EMAIL")
    if not destination_email:
        raise ValueError("The DESTINATION_EMAIL environment variable is not set.")
    await send_message(int(chat_id), f"Sucesso! Comprovante encaminhado para a imobiliaria às {current_time}. Enviado para o endereço: {destination_email}")
    
    return {"status": "success", "message": "Email sent"}