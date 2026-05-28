import os
import httpx
from dotenv import load_dotenv
import asyncio

load_dotenv()

async def get_telegram_file_bytes(file_id: str) -> bytes:
    """
    Baixa um arquivo do Telegram para a memória RAM a partir do seu file_id.
    
    Passos a implementar:
    1. Resgatar a variável de ambiente TELEGRAM_BOT_TOKEN.
    2. Construir a URL do método getFile e fazer um GET usando httpx.AsyncClient.
    3. Extrair o 'file_path' do JSON de resposta.
    4. Construir a URL final de download e fazer um novo GET.
    5. Retornar os bytes puros da resposta.
    """
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_bot_token:
        raise ValueError("A variável de ambiente TELEGRAM_BOT_TOKEN não está definida.")    
    
    get_file_url = f"https://api.telegram.org/bot{telegram_bot_token}/getFile?file_id={file_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(get_file_url)
        print(f"Resposta do getFile para file_id {file_id}: {response.json()}")
        file_path = response.json().get("result").get("file_path")
        
        download_url = f"https://api.telegram.org/file/bot{telegram_bot_token}/{file_path}"
        download_response = await client.get(download_url)
        print(f"Download do arquivo {file_id} concluído. Tamanho: {len(download_response.content)} bytes.")
        return download_response.content
