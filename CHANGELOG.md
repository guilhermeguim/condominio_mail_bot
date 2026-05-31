# Changelog

All notable changes to this project are documented in this file.

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