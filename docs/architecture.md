# Architecture Documentation: Condominio Mail Bot

This document covers the decoupled component design, non-blocking operational loops, and structural trade-offs implemented within the system.

## 1. High-Level Architectural Design
The solution is built on top of an event-driven architectural pattern utilizing a serverless deployment pipeline.

### Data Flow (Sequence Diagram)
```mermaid
sequenceDiagram
    autonumber
    participant User as Telegram User
    participant Telegram as Telegram API
    participant App as FastAPI (Cloud Run)
    participant Graph as MS Graph API

    User->>Telegram: Sends PDF receipt
    Telegram->>App: POST /webhook payload
    
    Note over App: 1. Security Validation
    App->>App: Validate ALLOWED_CHAT_IDS
    App->>App: Validate schema and PDF extension
    
    Note over App: 2. File Processing
    App->>Telegram: Request file stream
    Telegram-->>App: PDF Bytes (In-Memory)
    
    Note over App,Graph: 3. Email Dispatch
    App->>Graph: Authenticate and POST /me/sendMail
    Graph-->>App: 202 Accepted
    
    Note over App,User: 4. User Feedback
    App->>Telegram: POST /sendMessage (Success/Error)
    Telegram-->>User: Delivery confirmation message
    App-->>Telegram: 200 OK (Webhook ACK)
```

## 2. Decoupled Component Strategy
The codebase isolates core processing perimeters strictly to prevent cross-contamination across external infrastructure logic layers:

* **`main.py` (Ingress Orchestrator):** Acts as the central coordinator and first line of defense. It enforces strict access control via `ALLOWED_CHAT_IDS`, exposes a single `/webhook` POST route, absorbs raw JSON updates, offloads payload schema enforcement to Pydantic, executes the sequential business logic workflow, and dispatches bidirectional feedback to the user.
* **`schemas.py` (Perimeter Security):** Utilizes Pydantic v2 schemas to enforce strict structural typings, throwing rapid errors at the reverse proxy boundary if unmapped models hit the engine.
* **`telegram_client.py` (Inbound API Edge):** Encapsulates all interfaces toward the Telegram Bot API. Deals with file metadata checking, byte-stream generation, and outbound feedback messaging.
* **`email_service.py` (Outbound Delivery Layer):** Isolates the Microsoft Identity lifecycle. This layer abstracts token generation loops, OAuth token storage mechanisms, and base64 parsing.

## 3. Key Architectural Decisions
* **API REST Handshake over SMTP Relay:** Global identity security standards enforce the complete deprecation of basic authentication workflows for corporate and personal email endpoints. Shifting towards credentialed refresh token architectures via Microsoft Graph guarantees reliable compliance without hardcoded passwords.
* **Stateless Memory Buffer Isolation:** Hard block placed against file writing commands targeting persistent storage blocks or local disk temporary paths inside the Docker layout. Keeping the processing layout entirely in-memory prevents file access privilege bottlenecks, decreases latency, and blocks forensic document leaks if a container environment is compromised.