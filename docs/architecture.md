# Architecture Notes

This document describes how the current implementation is structured and how the main modules collaborate at runtime.

## Design Goal

The system is designed to be small, stateless, and easy to deploy in a serverless environment. The core workflow is simple:

- receive a Telegram webhook update
- identify whether it contains a supported file
- download the file without storing it locally
- forward the file by email

The implementation favors a thin API layer and isolated integration modules.

## Module Responsibilities

## `src/main.py`

This is the FastAPI entrypoint.

Its responsibilities are limited to:

- receiving the webhook request
- validating whether the incoming update contains a document
- enforcing the current PDF-only rule
- coordinating the Telegram download and email send steps

The module intentionally avoids embedding Telegram or Microsoft-specific request logic. That logic lives in dedicated service modules so it can be changed without rewriting the webhook handler.

## `src/schemas.py`

This module defines the Pydantic models used to validate the subset of Telegram's payload shape that matters to the application.

Instead of modeling the entire Telegram update schema, the project only keeps:

- the root `message`
- the nested `document`
- the `file_id`, `file_name`, and `mime_type` fields

This keeps the validation layer lean while still making the webhook contract explicit in code.

## `src/telegram_client.py`

This module handles the two-step Telegram file download flow.

Telegram does not provide the file bytes directly in the webhook payload. The application must:

1. call `getFile` with the `file_id`
2. read the returned `file_path`
3. request the file bytes from Telegram's file endpoint

The module returns raw bytes so the caller can decide what to do next. In the current project, those bytes are passed directly to the email service.

## `src/email_service.py`

This module owns outbound email delivery.

The current implementation uses Microsoft Graph rather than SMTP. At runtime, the service:

1. reads `MICROSOFT_CLIENT_ID` and `MICROSOFT_REFRESH_TOKEN`
2. uses MSAL to exchange the refresh token for an access token
3. base64-encodes the file bytes
4. constructs the `sendMail` request payload
5. sends the email with the attachment inline

Because Microsoft Graph expects attachments inside a JSON payload, the service never needs to create a temporary file.

## `src/get_token.py`

This is a setup-only helper script, not part of the production request path.

It uses the Microsoft device flow to bootstrap the refresh token stored in `.env`. The script is useful because the main API needs non-interactive authentication, while the first authorization still requires a user to sign in once.

## Runtime Sequence

## Inbound processing

1. Telegram calls `POST /webhook`.
2. FastAPI parses the request into `TelegramUpdateSchema`.
3. The handler checks whether the update contains a document.
4. The handler checks whether the document MIME type is `application/pdf`.
5. The handler sends the `file_id` to the Telegram client.
6. The Telegram client returns file bytes.
7. The handler sends those bytes and the filename to the email service.
8. The email service authenticates with Microsoft Graph and sends the message.
9. The API returns a small success or ignore response.

## Why in-memory processing matters

The code intentionally avoids writing attachments to disk.

That choice is helpful for this project because:

- it keeps the request flow simpler
- it avoids temp-file cleanup logic
- it aligns well with stateless container runtimes such as Cloud Run
- it reduces the chances of leaked files on the host filesystem

## Current Tradeoffs

Some design decisions are intentionally pragmatic but should be visible to anyone maintaining the project.

## Hardcoded email metadata

The recipient, subject, and message body are currently defined inside `src/email_service.py`.

That keeps the first implementation straightforward, but it also means behavioral changes require a code change instead of a configuration update.

## Microsoft Graph dependency

Even though the original design discussion may have considered SMTP, the code in this repository currently depends on:

- `msal`
- Microsoft Graph `sendMail`
- a stored refresh token

That is the behavior this repository documentation reflects.

## Validation scope

The webhook handler currently accepts only a narrow subset of Telegram events. Unsupported updates are ignored quickly, which is appropriate for a focused automation project but still worth documenting.

## Deployment Shape

The included Dockerfile packages the FastAPI application with Uvicorn and exposes port `8080`.

That shape matches platforms such as Google Cloud Run, where:

- the container must be stateless
- startup should be simple
- the application should listen on a public HTTP port

## Recommended Next Documentation Layers

If the project continues to grow, the next useful documentation layers would be:

- an operations guide for deployment and rollback
- an environment reference for all required variables
- an ADR-style note explaining why Graph was chosen over SMTP in the implemented version
