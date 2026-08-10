# Chameleon AI — Real-time Emotion Intelligence System

> **Zint AI Hackathon 2026** | Built by Daksh Pareek, Priyanshu Sharma, Sannidhi Paul

A real-time AI-powered customer sentiment analysis platform that detects customer emotions, auto-routes conversations, generates intelligent replies, and alerts human agents with millisecond latency.

---

## Live Demo Flow

```
Customer Input
        |
AI Emotion Detection (Score 0.0 to 1.0)
        |
  Score < 0.3          Score 0.3-0.7         Score > 0.7
      |                      |                     |
  ESCALATE                NORMAL                UPSELL
Human Agent Alert     Standard Bot Reply    Special Offer Sent
      |                      |                     |
 Saved to DB            Saved to DB           Saved to DB
```

---

## Features

| Feature | Description |
|---------|-------------|
| Real-time Sentiment Analysis | Evaluates emotion score (0.0 - 1.0) for each message |
| AI Bot Reply | Generates context-aware replies in English or Hindi |
| Escalation Alert | Triggers automated alerts when customer frustration is detected |
| Upsell Trigger | Issues promotional offers during positive interactions |
| Live Emotion Graph | Displays real-time area chart of emotion history |
| Conversation History | Maintains comprehensive conversation logs using SQLite |
| Bilingual Interface | Full support for English and Hindi |
| WebSocket Integration | Ensures real-time updates without page refreshes |

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| AI Model | Groq API — LLaMA 3.3 70B |
| Backend | Python FastAPI and WebSockets |
| Frontend | React, Vite, and Recharts |
| Database | SQLite |
| Styling | Custom CSS |

---

## Project Structure

```
smartcare-ai/
├── backend/
│   ├── main.py                  # FastAPI server and WebSocket implementation
│   ├── database.py              # SQLite initialization and operations
│   ├── ai/
│   │   ├── sentiment_classifier.py  # Emotion scoring and action routing
│   │   └── bot_reply.py             # AI reply generation logic
│   ├── .env                     # Environment variables and API keys
│   └── requirements.txt
├── frontend/
│   └── src/
│       └── App.jsx              # Main React dashboard component
└── docs/
    └── Readme.md                # Project documentation
```

---

## Setup & Execution Instructions

### Backend Configuration
```bash
cd backend
pip install fastapi uvicorn groq python-dotenv
# Ensure GROQ_API_KEY is added to the .env file
uvicorn main:app --reload
```

### Frontend Configuration
```bash
cd frontend
npm install
npm run dev
```

### Access Application
Navigate to `http://localhost:5173` in your web browser.

---

## Evaluation Criteria Alignment

| Criteria | Implementation Strategy |
|----------|-------------------------|
| Innovation & Creativity | Implements predictive emotion-based routing beyond standard chatbots |
| Real-World Problem Solving | Mitigates customer churn in SMEs resulting from inadequate support |
| Technical Architecture | Integrates WebSockets, FastAPI, React, SQLite, and Groq AI |
| Scalability | Designed with a stateless API architecture suitable for multi-tenant deployments |
| Documentation & Presentation | Includes comprehensive README, architecture documentation, and live demonstration |

---

## API Reference

| HTTP Method | Endpoint | Description |
|-------------|----------|-------------|
| POST | `/analyze` | Analyze message sentiment and generate reply |
| GET | `/history` | Retrieve complete conversation history from database |
| WS | `/ws` | Establish real-time WebSocket connection |

---

## Zint AI Hackathon 2026

Developed for the FlowZint AI Hackathon 2026 — National Level Innovation Challenge.

**Core Focus Areas:** Innovation, Scalability, AI Automation, Customer Engagement, and Intelligent Workflows.
