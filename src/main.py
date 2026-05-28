from fastapi import FastAPI
from dotenv import load_dotenv

# Importações dos nossos serviços isolados
from src.schemas import TelegramUpdateSchema
from src.telegram_client import get_telegram_file_bytes
from src.email_service import send_email_with_attachment

# Centraliza o carregamento do .env para todo o projeto
load_dotenv()

app = FastAPI(title="Condominio Mail Bot")

@app.post("/webhook")
async def telegram_webhook(update: TelegramUpdateSchema):

    if not update.message or not update.message.document:
        return {"status": "ignorado", "motivo": "Não é um documento"}
    
    if not update.message.document.mime_type or update.message.document.mime_type != "application/pdf":
        return {"status": "ignorado", "motivo": "Arquivo não é um PDF"}
    
    file_id = update.message.document.file_id
    file_name = update.message.document.file_name or "comprovante.pdf"
    
    file_bytes = await get_telegram_file_bytes(file_id)
    await send_email_with_attachment(file_bytes, file_name)
    
    return {"status": "sucesso", "mensagem": "E-mail enviado!"}