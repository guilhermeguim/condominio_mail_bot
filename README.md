# Condominio Mail Bot

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Latest-blue.svg?style=flat-square&logo=docker)](https://www.docker.com/)
[![Google Cloud Run](https://img.shields.io/badge/GCP-Cloud_Run-orange.svg?style=flat-square&logo=googlecloud)](https://cloud.google.com/run)
[![Microsoft Graph API](https://img.shields.io/badge/Microsoft-Graph_API-0078D4.svg?style=flat-square&logo=microsoft)](https://learn.microsoft.com/en-us/graph/)

A personal automation service designed to intercept Telegram attachments and route them directly to a Microsoft Outlook mailbox.

## Documentation Index
* **[Architecture & Design Decisions](docs/architecture.md):** Architectural choices, code decomposition, internal data flow, and trade-offs.
* **[Operations & Deployment Manual](docs/operations.md):** Complete guide to infrastructure provisioning on GCP, container management, and continuous updates.

## Project Purpose
Forwarding payment receipts from chat applications to email involves repetitive manual steps: downloading the file, opening the email client, writing a standard message, attaching the document, and sending it.

This project eliminates this friction. By acting as a webhook listener, it instantly captures PDF documents sent via Telegram and routes them directly to the specified inbox. The execution is purely in-memory, meaning no files are saved to disk, keeping the process fast, stateless, and secure.

## Local Development Quickstart

### 1. Prerequisites
* Python 3.11+
* Active virtual environment
* Ngrok account and binary installed

### 2. Telegram Bot Creation
1. Open Telegram, search for @BotFather and start a conversation.
2. Send the command `/newbot` and follow the instructions to choose a name and username.
3. Save the HTTP API Token provided at the end of the creation.

### 3. Microsoft Azure AD Configuration
To send emails via Microsoft Graph using a personal account (Outlook/Hotmail), follow these registration steps:
1. Access the Microsoft Azure Portal, navigate to Microsoft Entra ID, and select App registrations.
2. Create a new registration. In the Supported account types section, you must select: Accounts in any organizational directory and personal Microsoft accounts.
3. Under Authentication, add the Mobile and desktop applications platform and select the default native redirect URI (`https://login.microsoftonline.com/common/oauth2/nativeclient`).
4. Under API permissions, add the following Delegated permission for Microsoft Graph: `Mail.Send`. Click on Grant admin consent if applicable.
5. Copy your Application (client) ID from the overview page.
6. Note on Credentials: Since this application uses the MSAL Public Client flow via Device Code, you do not need and should not generate a Client Secret. Authentication relies strictly on user consent and the generated Refresh Token.

### 4. Installation & Token Generation
Clone the repository and install the required dependencies:
```bash
git clone [https://github.com/guilhermeguim/condominio_mail_bot.git](https://github.com/guilhermeguim/condominio_mail_bot.git)
cd condominio_mail_bot
pip install -r requirements.txt
```

To generate your offline Refresh Token, run the helper script and follow the terminal instructions to link your personal account:
```bash
python src/get_token.py
```
Save the output Refresh Token string.

### 5. Environment Configuration
Create a local `.env` file in the root directory:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
MICROSOFT_CLIENT_ID=your_azure_client_id_here
MICROSOFT_TENANT_ID=consumers
MICROSOFT_REFRESH_TOKEN=your_oauth2_refresh_token_here
```
Note: The `MICROSOFT_TENANT_ID` must be configured as `consumers` to allow authentication via personal Microsoft accounts.

### 6. Local Webhook Tunnelling (Ngrok)
Telegram webhooks require a public HTTPS URL to reach your local server:
1. Start Ngrok in a separate terminal pointing to port 8080:
```bash
ngrok http 8080
```
2. Copy the secure forwarding URL (e.g., `https://xxxx.ngrok-free.app`).
3. Set your Telegram webhook by replacing the tokens in the following URL structure and executing it in your browser:
```text
[https://api.telegram.org/bot](https://api.telegram.org/bot)<YOUR_TELEGRAM_TOKEN>/setWebhook?url=[https://xxxx.ngrok-free.app/webhook](https://xxxx.ngrok-free.app/webhook)
```

### 7. Local Execution
Launch the local asynchronous ASGI server:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```
The endpoint is now live. Sending a PDF to your Telegram bot will trigger the local loop, discharging the email via Microsoft Graph API.