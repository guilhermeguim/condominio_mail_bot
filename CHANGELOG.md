# Changelog

All notable changes to this project are documented in this file.

## v1.1.2 - 2026-05-31

### Changed

- Moved the outbound email subject and body from source code into the `EMAIL_SUBJECT` and `EMAIL_BODY` environment variables.
- Updated the README and operations guide to document the new runtime configuration.

### Fixed

- Converted escaped `\n` sequences from `EMAIL_BODY` into real line breaks before sending the message through Microsoft Graph.

## v1.1.1 - 2026-05-31

### Fixed

- Corrected the Telegram success message timestamp to use Brasilia time instead of the container default timezone.
- Added a safe UTC-3 fallback for environments where IANA timezone data is unavailable.

## v1.1.0 - 2026-05-31

### Added

- Chat whitelist enforcement through the `ALLOWED_CHAT_IDS` environment variable.
- Telegram chat feedback for success, invalid file submissions, and missing document submissions.
- `send_message` support in the Telegram client for outbound user notifications.
- Chat metadata support in the Telegram webhook schemas.

### Changed

- Updated the webhook flow to fail fast for unauthorized chats before any file download work begins.
- Expanded the README, architecture notes, and operations guide to document the new webhook security behavior and Cloud Run scaling limits.
- Refreshed inline guidance and docstrings around the webhook, Telegram client, and email delivery flow.

### Fixed

- Reduced unnecessary processing for unauthorized or unsupported webhook requests.

## v1.0.0 - 2026-05-31

### Added

- Initial FastAPI webhook for Telegram document updates.
- Telegram file download flow that keeps attachments in memory.
- Microsoft Graph email delivery with attachment support.
- Dockerfile for container-based local runs and Cloud Run deployment.
- Central project documentation, architecture notes, and operations manual.

### Changed

- Improved inline code documentation and module-level guidance across the codebase.
- Refined project documentation structure for public portfolio presentation.
- Moved the destination email address from source code to the `DESTINATION_EMAIL` environment variable.

### Fixed

- Refined the outbound email body copy.
- Removed the hardcoded recipient address from the email delivery flow.