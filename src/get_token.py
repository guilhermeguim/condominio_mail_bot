import os
import msal
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("MICROSOFT_CLIENT_ID")
# Para contas pessoais, a autoridade é 'consumers'
app = msal.PublicClientApplication(client_id, authority="https://login.microsoftonline.com/consumers")

# Iniciamos o fluxo pedindo permissão para ler enviar emails e manter o acesso offline (Refresh Token)
# Pedimos apenas o Mail.Send, e o msal inclui o offline_access automaticamente!
flow = app.initiate_device_flow(scopes=["Mail.Send"])

if "user_code" not in flow:
    raise ValueError("Falha ao criar o fluxo de dispositivo. Verifique as credenciais.")

print(flow["message"]) # O terminal vai te dar um código e um link (https://microsoft.com/devicelogin)

# O script vai pausar aqui e esperar você logar no navegador
result = app.acquire_token_by_device_flow(flow)

if "refresh_token" in result:
    print("\nSUCESSO! Copie a linha abaixo e cole no seu .env:")
    print(f"MICROSOFT_REFRESH_TOKEN={result['refresh_token']}")
else:
    print("Erro ao obter token:", result.get("error_description"))