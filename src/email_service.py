"""Send proof-of-payment emails through Microsoft Graph.

This module isolates everything related to outbound email delivery. The webhook
handler only needs to provide the file bytes and a filename; this module takes
care of turning those inputs into the JSON payload expected by Microsoft Graph,
requesting an access token, and submitting the final API call.
"""

import base64
import os
import textwrap

import httpx
import msal
from dotenv import load_dotenv

load_dotenv()

GRAPH_AUTHORITY = "https://login.microsoftonline.com/consumers"
GRAPH_SEND_MAIL_URL = "https://graph.microsoft.com/v1.0/me/sendMail"


async def get_graph_access_token() -> str:
    """Exchange the stored refresh token for a Microsoft Graph access token.

    The application keeps a long-lived refresh token in the environment so the
    webhook can authenticate without any interactive login. For each outbound
    email, this function asks Microsoft for a fresh short-lived access token
    scoped to ``Mail.Send``.

    Returns:
        A bearer token that can be sent in the Authorization header of the
        Microsoft Graph ``sendMail`` request.

    Raises:
        ValueError: If the required environment variables are missing or if the
            token refresh request does not return an ``access_token`` field.
    """
    # Read the client ID at call time so misconfiguration surfaces immediately when the email workflow runs.
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    if not client_id:
        raise ValueError("The MICROSOFT_CLIENT_ID environment variable is not set.")
    
    # The refresh token is what allows the service to obtain a new access token without sending the operator through a browser login flow again.
    refresh_token = os.getenv("MICROSOFT_REFRESH_TOKEN")
    if not refresh_token:
        raise ValueError("The MICROSOFT_REFRESH_TOKEN environment variable is not set.")
    
    # MSAL knows how to talk to Microsoft's consumer tenant and perform the refresh-token exchange expected by personal Outlook accounts.
    app = msal.PublicClientApplication(client_id=client_id, authority=GRAPH_AUTHORITY)

    # Only ``Mail.Send`` is requested because this service never reads mailbox contents; it only needs permission to send a prepared message.
    result = app.acquire_token_by_refresh_token(refresh_token, scopes=["Mail.Send"])

    # A successful response includes ``access_token``. Any other shape means the token exchange failed and the caller should not attempt to send the email.
    if "access_token" in result:
        return result["access_token"]

    raise ValueError(
        "Unable to get a Microsoft Graph access token: "
        f"{result.get('error_description', 'No error description was returned.')}"
    )


async def send_email_with_attachment(file_bytes: bytes, filename: str) -> None:
    """Send an email with an attachment that already lives in memory.

    The webhook downloads files from Telegram directly into RAM. This function
    keeps that approach all the way through email delivery by converting the raw
    bytes into the base64 representation required by Microsoft Graph and sending
    the message without writing anything to disk.

    Args:
        file_bytes: Raw contents of the file received from Telegram.
        filename: Name that should appear on the email attachment.

    Raises:
        ValueError: If the Graph access token cannot be obtained or if the
            destination email environment variable is missing.
        httpx.HTTPStatusError: If Microsoft Graph rejects the outbound request.
    """
    # Read the destination email at call time to ensure no hardcoded values
    # remain in the codebase and misconfigurations fail fast.
    destination_email = os.getenv("DESTINATION_EMAIL")
    if not destination_email:
        raise ValueError("The DESTINATION_EMAIL environment variable is not set.")

    # Every send operation starts by obtaining a fresh bearer token so the request is authorized with current credentials.
    access_token = await get_graph_access_token()
    
    # Graph expects binary attachments inside JSON, so the raw bytes must be converted to a base64 string before they can be embedded in the payload.
    attachment_content_b64 = base64.b64encode(file_bytes).decode('utf-8')
    
    # ``dedent`` keeps the email body readable in source control without leaking Python indentation into the final message text.
    email_body = textwrap.dedent("""\
        Bom dia!!

        Segue em anexo o comprovante de pagamento de condômino do mês. Em nome da proprietária Sonia Guim.

        Guilherme Guim
        19 98885-1020
    """).strip()
    
    # The payload below follows the structure documented for Graph's ``/me/sendMail`` endpoint. Keeping it explicit makes the wire format easy to inspect when the integration needs maintenance.
    payload = {
        "message": {
            "subject": "COMPROVANTE DE PAGAMENTO DE CONDOMÍNIO - Sonia Guim",
            "body": {
                "contentType": "Text",
                "content": email_body
            },
            # Graph always expects a list of recipients, even when the message is sent to a single mailbox. We use the dynamically loaded env var.
            "toRecipients": [
                {
                    "emailAddress": { "address": destination_email }
                }
            ],
            # The attachment metadata is sent inline with the message payload. ``contentBytes`` must contain the base64-encoded file contents.
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

    # The access token travels in the Authorization header. The explicit content type makes it clear that the request body is JSON.
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # Graph answers with HTTP 202 when the send request is accepted. Any 4xx or 5xx response should fail fast so the webhook can surface the error.
        response = await client.post(GRAPH_SEND_MAIL_URL, headers=headers, json=payload)
        response.raise_for_status()