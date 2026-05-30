"""Define the subset of Telegram webhook payloads used by the application.

Telegram sends a large and deeply nested JSON structure. These models only keep
the fields that the webhook handler actually reads, which makes validation more
focused while still documenting the shape the application depends on.
"""

from pydantic import BaseModel, Field


class DocumentSchema(BaseModel):
    """Represent the document metadata nested inside a Telegram message.

    Only three fields are needed for this workflow:

    - ``file_id`` identifies the file when calling Telegram's download API.
    - ``file_name`` is reused as the outbound email attachment name.
    - ``mime_type`` is checked to enforce the PDF-only rule.
    """

    file_id: str = Field(
        ...,
        description="Opaque Telegram identifier used later to resolve the real file path.",
    )
    file_name: str | None = Field(
        default=None,
        description="Original filename reported by Telegram, when available.",
    )
    mime_type: str | None = Field(
        default=None,
        description="MIME type supplied by Telegram for the uploaded document.",
    )
    

class MessageSchema(BaseModel):
    """Represent the message section of the Telegram update.

    The project only reads the ``document`` field, so the model intentionally
    ignores the many other message attributes Telegram can include.
    """

    document: DocumentSchema | None = Field(
        default=None,
        description="Document payload when the Telegram message contains a file.",
    )


class TelegramUpdateSchema(BaseModel):
    """Represent the root webhook payload sent by Telegram.

    Telegram may include callback queries, edited messages, and other update
    types. For this project, the ``message`` branch is the only one required.
    """

    message: MessageSchema | None = Field(
        default=None,
        description="Message branch of the update when the event is a standard chat message.",
    )