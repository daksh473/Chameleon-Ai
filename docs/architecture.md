# Chameleon AI — Architecture Documentation

## System Overview

Chameleon AI is a real-time customer emotion intelligence platform. It analyzes incoming customer messages, detects sentiment, generates context-aware replies, and triggers automated actions — all within milliseconds via WebSocket.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                      │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 3D Robot │  │ Live Graph │  │  Stats   │  │  Chat UI │  │
│  │(CSS 3D)  │  │(Recharts)  │  │Dashboard │  │+ Alert   │  │
│  └──────────┘  └────────────┘  └──────────┘  └──────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │ WebSocket (ws://localhost:8000/ws)
                        │ Real-time bidirectional
┌───────────────────────▼─────────────────────────────────────┐
│                    BACKEND (FastAPI)                          │
│                                                              │
│   /ws endpoint          /analyze endpoint    /history        │
│   WebSocket server      REST API             GET all DB      │
│         │                    │                               │
│         ▼                    ▼                               │
│   ┌─────────────────────────────────┐                        │
│   │         AI Processing Layer     │                        │
│   │                                 │                        │
│   │  sentiment_classifier.py        │                        │
│   │  → Groq LLaMA 3.3 70B          │                        │
│   │  → Returns: score, emotion      │                        │
│   │                                 │                        │
│   │  decide_action(score)           │                        │
│   │  → score < 0.3  → ESCALATE     │                        │
│   │  → score 0.3–0.7 → NORMAL      │                        │
│   │  → score > 0.7  → UPSELL       │                        │
│   │                                 │                        │
│   │  bot_reply.py                   │                        │
│   │  → Groq LLaMA 3.3 70B          │                        │
│   │  → Context-aware reply          │                        │
│   │  → Hindi + English support      │                        │
│   └─────────────┬───────────────────┘                        │
│                 │                                            │
│                 ▼                                            │
│   ┌─────────────────────┐                                    │
│   │   database.py       │                                    │
│   │   SQLite DB         │                                    │
│   │   → save_conversation()                                  │
│   │   → get_all_conversations()                              │
│   └─────────────────────┘                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### WebSocket Flow (Real-time)
```
1. Customer types message in React UI
2. WebSocket sends raw text to FastAPI /ws
3. sentiment_classifier.py → Groq API → returns {score, emotion}
4. decide_action(score) → returns ESCALATE / NORMAL / UPSELL
5. bot_reply.py → Groq API → returns contextual reply
6. save_conversation() → SQLite DB
7. JSON response sent back via WebSocket
8. React UI updates: graph, stats, card, alert (if ESCALATE)
```

### Response JSON Schema
```json
{
  "message": "Customer's original message",
  "score": 0.05,
  "emotion": "angry",
  "action": "ESCALATE",
  "reply": "Bot's contextual reply in same language"
}
```

---

## AI Design Decisions

### Why Groq + LLaMA 3.3 70B?
- Free tier available — no cost for hackathon
- Extremely fast inference (< 1 second)
- Multilingual — handles Hindi and English natively
- Large context window for nuanced sentiment detection

### Sentiment Scoring
- Temperature = 0 for consistent, deterministic output
- JSON-only response format for reliable parsing
- Score range 0.0–1.0 maps directly to emotion intensity

### Bot Reply Prompting
- Three separate system prompts per action type
- Language detection is implicit — model matches customer language
- Max 100 tokens keeps replies concise and actionable

---

## Database Schema

```sql
CREATE TABLE conversations (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    message   TEXT NOT NULL,
    score     REAL NOT NULL,
    emotion   TEXT NOT NULL,
    action    TEXT NOT NULL,
    reply     TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
```

---

## Scalability Considerations

| Concern | Current Solution | Scale Solution |
|---------|-----------------|----------------|
| Multiple users | Single WebSocket | WebSocket rooms per session |
| DB performance | SQLite | PostgreSQL / Redis |
| AI latency | Groq free tier | Groq paid / dedicated |
| Frontend | Vite dev server | Build + CDN deploy |

---

## Security Notes
- API keys stored in `.env` — never committed to Git
- CORS middleware configured for controlled access
- Input sanitization handled at FastAPI Pydantic layer