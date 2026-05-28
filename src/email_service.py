import os
import base64
import httpx
import msal
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def get_graph_access_token() -> str:
    """
    1. Resgatar MICROSOFT_CLIENT_ID e MICROSOFT_REFRESH_TOKEN do os.getenv().
    2. Instanciar msal.PublicClientApplication passando o client_id e authority="https://login.microsoftonline.com/consumers".
    3. Chamar o método acquire_token_by_refresh_token(refresh_token, scopes=["Mail.Send"]) da instância msal.
    4. Se a chave 'access_token' estiver no dicionário de resposta, retorná-la. Senão, levantar um ValueError.
    """
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    if not client_id:
        raise ValueError("A variável de ambiente MICROSOFT_CLIENT_ID não está definida.")
    
    refresh_token = os.getenv("MICROSOFT_REFRESH_TOKEN")
    if not refresh_token:
        raise ValueError("A variável de ambiente MICROSOFT_REFRESH_TOKEN não está definida.")
    
    tenant_id = "consumers"  # Para contas pessoais da Microsoft
    
    app = msal.PublicClientApplication(client_id=client_id, authority=f"https://login.microsoftonline.com/{tenant_id}")
    result = app.acquire_token_by_refresh_token(refresh_token, scopes=["Mail.Send"])
    if "access_token" in result:
        return result["access_token"]

    else:
        raise ValueError(f"Erro ao obter access token: {result.get('error_description', 'Sem descrição de erro')}")
    
    
    
async def send_email_with_attachment(file_bytes: bytes, filename: str) -> None:
    """
    Envia o e-mail via Microsoft Graph API usando httpx de forma assíncrona.
    
    1. Obter o access_token chamando a função get_graph_access_token().
    2. Converter os file_bytes para uma string Base64. 
       (Dica: use base64.b64encode(file_bytes).decode('utf-8'))
    3. Montar o dicionário Python (payload) com a estrutura exigida pelo Graph API (veja abaixo).
    4. Instanciar um httpx.AsyncClient() e fazer um POST para 'https://graph.microsoft.com/v1.0/me/sendMail'.
    5. Passar os headers={"Authorization": f"Bearer {access_token}"} e o json=seu_dicionario_payload.
    """    
    access_token = await get_graph_access_token()
    
    attachment_content_b64 = base64.b64encode(file_bytes).decode('utf-8')
    
    # Montar o payload
    payload = {
        "message": {
            "subject": "COMPROVANTE DE PAGAMENTO DE CONDOMÍNIO - Sonia Guim",
            "body": {
                "contentType": "Text",
                "content": "Segue em anexo o comprovante de pagamento do condomínio. Obrigado!"
            },
            "toRecipients": [
                {
                    "emailAddress": { "address": "gapguim@gmail.com" }
                }
            ],
            "attachments": [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": filename,
                    "contentBytes": attachment_content_b64 
                }
            ]
        },
        "saveToSentItems": "true"
    }

    url = 'https://graph.microsoft.com/v1.0/me/sendMail'
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Levanta um erro se a resposta for 4xx ou 5xx
        