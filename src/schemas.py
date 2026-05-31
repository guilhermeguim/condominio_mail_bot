"""Define the subset of Telegram webhook fields required by the application.

Telegram delivers a much larger payload than this project needs. These models
focus on the small slice of the schema used by the webhook: the originating chat
identifier for access control and the document metadata required for validation
and download.
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
    
    
class ChatSchema(BaseModel):
    """Represent the chat metadata attached to an inbound Telegram message.

    The webhook uses the chat ID as the source of truth for the whitelist check
    and for routing success or failure notifications back to the same chat.
    """

    id: int = Field(
        ...,
        description="Unique identifier for this chat.",
    )

class MessageSchema(BaseModel):
    """Represent the message section of the Telegram update.

    The current webhook relies on two branches of the message payload:

    - ``chat`` to identify who sent the update.
    - ``document`` to inspect and process the uploaded file.

    The rest of Telegram's message attributes remain intentionally out of scope.
    """

    chat: ChatSchema | None = Field(
        default=None,
        description="Chat branch containing the chat ID.",
    )

    document: DocumentSchema | None = Field(
        default=None,
        description="Document payload when the Telegram message contains a file.",
    )


class TelegramUpdateSchema(BaseModel):
    """Represent the root webhook payload sent by Telegram.

    Telegram may include callback queries, edited messages, and other update
    types. For this project, the ``message`` branch is the only one read by the
    application runtime.
    """

    message: MessageSchema | None = Field(
        default=None,
        description="Message branch of the update when the event is a standard chat message.",
    )
