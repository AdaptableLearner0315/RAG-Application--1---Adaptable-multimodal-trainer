# CLAUDE.md - Project Context for AI Assistants

> **Version**: V0 (Functional MVP)
> **Last Updated**: 2026-02-01
> **Next Focus**: User Experience Enhancement for Power Users

---

## Project Overview

**Adaptive Adolescent Coaching Platform (AACP)** - A multi-agent RAG application providing holistic health coaching (nutrition, fitness, recovery) for adolescents aged 16-19.

**Core Differentiator**: Three-tier memory system with query-aware retrieval that learns and adapts over time.

**Target Power User**: Neha - Teen athlete seeking personalized, adaptive coaching that feels like chatting with a knowledgeable friend.

---

## V0 Status: What's Built

| Component | Status | Description |
|-----------|--------|-------------|
| Multi-Agent System | ✅ | Trainer, Nutritionist, Recovery coaches |
| Three-Tier Memory | ✅ | Working, Short-term, Long-term |
| Auto Model Routing | ✅ | Haiku/Sonnet/Opus based on complexity |
| Voice Input | ✅ | Whisper transcription |
| Image Analysis | ✅ | Food photo analysis via Claude Vision |
| Conversational Prompts | ✅ | Friendly, teen-appropriate tone |
| Safety Checks | ✅ | Harmful content filtering |
| User Profiles | ✅ | Injuries, allergies, goals |

---

## UX Improvement Roadmap (Making Neha a Power User)

### Phase 1: Onboarding Experience
- [ ] Guided onboarding wizard (not just text input)
- [ ] Visual goal selection (muscle building, weight loss, etc.)
- [ ] Injury/allergy picker with common options
- [ ] Profile photo and personalization

### Phase 2: Conversation Flow
- [ ] Quick action buttons ("Log meal", "Start workout", "Check sleep")
- [ ] Suggested follow-ups after each response
- [ ] Progress indicators (weekly streaks, goals met)
- [ ] Rich message formatting (tables, charts for macros)

### Phase 3: Engagement & Retention
- [ ] Daily check-ins with push notifications
- [ ] Weekly progress summaries
- [ ] Achievement badges and milestones
- [ ] Workout/meal plan scheduling

### Phase 4: Advanced Features
- [ ] Workout timer with rest period alerts
- [ ] Meal prep reminders
- [ ] Sleep schedule optimization
- [ ] Integration with fitness trackers (future)

### Phase 5: Social & Community
- [ ] Share progress with friends
- [ ] Community challenges
- [ ] Leaderboards (optional)

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | React + Next.js 14 | App router, Tailwind CSS |
| Backend | Python + FastAPI | Async, Pydantic validation |
| Agent Orchestration | LangGraph | StateGraph for multi-agent workflow |
| LLM | Claude (Haiku/Sonnet/Opus) | Auto-routed by complexity |
| Embeddings | sentence-transformers | all-MiniLM-L6-v2 (local, free) |
| Vector Store | ChromaDB | Local persistence |
| Database | SQLite | Memory persistence |
| Cache | Redis | With in-memory fallback |
| Speech-to-Text | Whisper API | OpenAI |
| Testing | pytest / Jest | Backend / Frontend |

---

## Project Structure

```
RAG Applicaion/
├── backend/
│   ├── app/
│   │   ├── core/           # Config, exceptions, utilities
│   │   ├── memory/         # Three-tier memory system
│   │   ├── retrieval/      # RAG pipeline (embed, search)
│   │   ├── ingestion/      # Document loading, chunking
│   │   ├── tools/          # Agent tools (food DB, exercise DB)
│   │   ├── input/          # Voice, image, text processing
│   │   ├── agents/         # LangGraph agents + model router
│   │   └── api/            # FastAPI routes
│   └── tests/
│       ├── unit/           # Unit tests (93+ tests)
│       ├── integration/    # Cross-module tests (19 tests)
│       └── e2e/            # End-to-end tests (7 tests)
├── frontend/
│   └── src/
│       ├── app/            # Pages (page.tsx, layout.tsx)
│       ├── components/     # Chat, VoiceInput, ImageUpload
│       ├── hooks/          # useChat, useVoice
│       └── lib/            # API client, HTTP utilities
├── notes/                  # Project notes & changelog
├── PRD.md                  # Product requirements
├── SYSTEM_DESIGN.md        # Technical design
└── CLAUDE.md               # This file
```

---

## Key Architecture

### Auto Model Routing
```
┌─────────────────────────────────────────────────────────┐
│                    MODEL ROUTER                          │
├─────────────────────────────────────────────────────────┤
│  "Hi" / "Thanks"  →  Haiku (fast, cheap)               │
│  "What to eat?"   →  Sonnet (balanced)                 │
│  "Weekly plan"    →  Opus (complex reasoning)          │
└─────────────────────────────────────────────────────────┘
```

### Multi-Agent System
```
         ┌──────────────┐
         │ MODEL ROUTER │ ← Selects LLM
         └──────┬───────┘
                ▼
         ┌──────────────┐
         │ AGENT ROUTER │ ← Classifies intent
         └──────┬───────┘
      ┌─────────┼─────────┐
      ▼         ▼         ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ TRAINER │ │NUTRITION│ │RECOVERY │
└────┬────┘ └────┬────┘ └────┬────┘
      └─────────┼─────────┘
                ▼
         ┌──────────────┐
         │    MERGE     │ → Combined response
         └──────────────┘
```

### Three-Tier Memory
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   WORKING   │    │  SHORT-TERM  │    │  LONG-TERM  │
│   (Redis)   │    │   (SQLite)   │    │  (SQLite)   │
├─────────────┤    ├──────────────┤    ├─────────────┤
│ Last 5 msgs │    │ 7-day window │    │ Permanent   │
│ Session ctx │    │ Meals, sleep │    │ Profile     │
│ 500 tokens  │    │ 800 tokens   │    │ 400 tokens  │
└─────────────┘    └──────────────┘    └─────────────┘
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Multi-agent chat with auto model routing |
| `/api/voice/transcribe` | POST | Whisper audio transcription |
| `/api/image/analyze` | POST | Claude Vision food analysis |
| `/api/profile/{user_id}` | GET/POST/PUT/DELETE | User profile CRUD |
| `/health` | GET | Application health check |

---

## Recent Refactoring (V0)

### Backend
- **Centralized exceptions** (`app/core/exceptions.py`) - Hierarchical error classes
- **Model router** (`app/agents/model_router.py`) - Auto LLM selection
- **Greeting handler** - Single response for simple queries
- **Conversational prompts** - Friendly, teen-appropriate tone

### Frontend
- **HTTP client** (`lib/http.ts`) - Centralized fetch with error handling
- **Refactored API** (`lib/api.ts`) - Clean, typed API calls
- **Removed manual model selector** - Now auto-selected by backend

---

## Commands

```bash
# Start backend
cd backend && uvicorn app.main:app --reload --port 8000

# Start frontend
cd frontend && npm run dev

# Run all tests
cd backend && pytest tests/ -v

# Build frontend
cd frontend && npm run build
```

---

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=     # For Claude LLM
OPENAI_API_KEY=        # For Whisper STT

# Optional
REDIS_HOST=localhost
REDIS_PORT=6379
DEBUG=false
```

---

## For Claude: Planning Next Steps

When planning UX improvements for Neha:

1. **Understand her journey**: New user → Regular user → Power user
2. **Reduce friction**: Quick actions > typing, visual > text
3. **Build habits**: Streaks, reminders, progress tracking
4. **Personalize**: Remember preferences, adapt to patterns
5. **Delight**: Celebrate wins, encouraging tone, fun interactions

### Key Questions to Explore
- How does Neha typically interact with the app? (Morning check-in? Post-workout?)
- What makes her come back daily?
- What frustrates her about current health apps?
- How can we make logging meals/workouts feel rewarding, not tedious?

---

## Repository

**GitHub**: https://github.com/AdaptableLearner0315/RAG-Application--1---Adaptable-multimodal-trainer.git

---

## Notes

See `notes/` directory for:
- `CHANGELOG.md` - Version history
- `BUILD_LOG.md` - Development decisions
