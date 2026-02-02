# CLAUDE.md - Project Context for AI Assistants

> **Last Updated**: 2026-02-01
> **Change Log**: See `notes/CHANGELOG.md` for detailed history

---

## Project Overview

**Adaptive Adolescent Coaching Platform (AACP)** - A multi-agent RAG application providing holistic health coaching (nutrition, fitness, recovery) for adolescents aged 16-19.

**Core Differentiator**: Three-tier memory system with query-aware retrieval that learns and adapts over time.

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | React + Next.js 14 | App router, Tailwind CSS |
| Backend | Python + FastAPI | Async, Pydantic validation |
| Agent Orchestration | LangGraph | StateGraph for multi-agent workflow |
| LLM | Claude Sonnet 4 | Reasoning + Vision capabilities |
| Embeddings | sentence-transformers | all-MiniLM-L6-v2 (local, free) |
| Vector Store | ChromaDB | Local persistence |
| Database | SQLite | Memory persistence |
| Cache | Redis | With in-memory fallback |
| Speech-to-Text | Whisper API | OpenAI |
| Observability | Langfuse | Self-hosted (free) |
| Testing | pytest / Jest | Backend / Frontend |

---

## Project Structure

```
RAG Applicaion/
├── backend/
│   ├── app/
│   │   ├── core/           # ✅ Config, utilities
│   │   ├── memory/         # ✅ Three-tier memory system
│   │   ├── retrieval/      # ✅ RAG pipeline (embed, search)
│   │   ├── ingestion/      # ✅ Document loading, chunking
│   │   ├── tools/          # ✅ Agent tools (food DB, exercise DB)
│   │   ├── input/          # ✅ Voice, image, text processing
│   │   ├── agents/         # ✅ LangGraph agents
│   │   └── api/            # ✅ FastAPI routes
│   └── tests/
│       ├── unit/           # ✅ Unit tests (84+ tests)
│       ├── integration/    # ✅ Cross-module tests (19 tests)
│       └── e2e/            # ✅ End-to-end tests (7 tests)
├── frontend/               # ✅ Next.js app
│   └── src/
│       ├── app/            # Pages (page.tsx, layout.tsx)
│       ├── components/     # Chat, VoiceInput, ImageUpload
│       ├── hooks/          # useChat, useVoice
│       └── lib/            # API client
├── notes/                  # 📝 Project notes & changelog
│   ├── CHANGELOG.md        # CLAUDE.md change history
│   └── BUILD_LOG.md        # Detailed build log
├── PRD.md                  # Product requirements
├── SYSTEM_DESIGN.md        # Technical design
└── CLAUDE.md               # This file
```

---

## Build Status

| Module | Status | Tests | Key Files |
|--------|--------|-------|-----------|
| Memory | ✅ Complete | 20 | schemas.py, working.py, short_term.py, long_term.py, retriever.py |
| Retrieval | ✅ Complete | 10 | embedder.py, vectorstore.py, search.py |
| Ingestion | ✅ Complete | 10 | loader.py, chunker.py |
| Tools | ✅ Complete | 10 | food_db.py, exercise_db.py, calculators.py |
| Input | ✅ Complete | 10 | voice.py, image.py, text.py |
| Agents | ✅ Complete | 10 | router.py, trainer.py, nutritionist.py, recovery.py, graph.py |
| API Routes | ✅ Complete | 14 | main.py, deps.py, chat.py, voice.py, image.py, profile.py |
| Frontend | ✅ Complete | - | Chat.tsx, VoiceInput.tsx, ImageUpload.tsx |
| Integration | ✅ Complete | 19 | test_memory_retrieval.py, test_input_agents.py, test_api_flow.py |
| E2E | ✅ Complete | 7 | test_user_journeys.py |

**Total Tests**: 176 passing (unit + integration + e2e)

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Multi-agent chat with safety checks |
| `/api/voice/transcribe` | POST | Whisper audio transcription |
| `/api/image/analyze` | POST | Claude Vision food analysis |
| `/api/profile/{user_id}` | GET/POST/PUT/DELETE | User profile CRUD |
| `/api/profile/{user_id}/injury` | POST | Add injury to profile |
| `/health` | GET | Application health check |

---

## Key Architecture Decisions

### 1. Three-Tier Memory System
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

### 2. Query-Aware Memory Retrieval
Memory retriever analyzes query intent and fetches only relevant context:
- **Workout query** → injuries, recent workouts, fitness level
- **Food query** → intolerances, recent meals, dietary preferences
- **Sleep query** → sleep logs, recent workouts

### 3. Multi-Agent Architecture (LangGraph)
```
           ┌─────────┐
           │ ROUTER  │ ← Classifies intent
           └────┬────┘
      ┌─────────┼─────────┐
      ▼         ▼         ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ TRAINER │ │NUTRITION│ │RECOVERY │
└────┬────┘ └────┬────┘ └────┬────┘
      └─────────┼─────────┘
                ▼
           ┌─────────┐
           │  MERGE  │ → Combined response
           └─────────┘
```

### 4. No Fine-tuning Policy
All personalization achieved via:
- RAG retrieval from knowledge base
- Tool calling for real-time data (USDA, exercise DBs)
- Prompt injection with user memory context

---

## Development Patterns

### Module Structure
```python
# One class per file, <100 lines
# Docstrings on every function
# Type hints throughout
# 5 edge cases per component
```

### Testing Strategy
- Unit tests first, then integration
- Test file mirrors source structure
- Mock external dependencies

### Git Workflow
- Feature branches per module
- Worktrees for parallel development (3 max)
- Merge to main only after tests pass

---

## Commands

```bash
# Backend
cd backend

# Run all unit tests
pytest tests/unit/ -v

# Run specific module tests
pytest tests/unit/test_memory/ -v

# Run with coverage
pytest --cov=app tests/

# Start API server
uvicorn app.main:app --reload

# Frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

---

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=     # For Claude LLM
OPENAI_API_KEY=        # For Whisper STT

# Optional
REDIS_HOST=localhost   # Falls back to in-memory
REDIS_PORT=6379
DEBUG=false            # Enable debug logging
API_PORT=8000
```

---

## Free APIs Used

| API | Purpose | Rate Limits |
|-----|---------|-------------|
| USDA FoodData Central | Nutrition lookup | 1000/hour |
| wger.de | Exercise database | Unlimited |
| DuckDuckGo Search | Web fallback | Reasonable use |

---

## Current Sprint

**Status**: All modules and tests complete

**Next Steps**:
1. [x] Integration Tests - Cross-module testing (19 tests)
2. [x] E2E Tests - Full conversation flow (7 tests)
3. [ ] Local Deployment - Run application locally
4. [ ] Git Push - Push to remote repository

---

## Completed Phases

| Phase | Modules | Tests | Date |
|-------|---------|-------|------|
| Phase 1 | Memory, Retrieval, Ingestion | 40 | 2026-02-01 |
| Phase 2 | Tools, Input, Agents | 30 | 2026-02-01 |
| Phase 3 | API Routes, Frontend | 14 | 2026-02-01 |
| Phase 4 | Integration Tests, E2E Tests | 26 | 2026-02-01 |

---

## Notes Directory

For detailed logs and history, see the `notes/` directory:
- `notes/CHANGELOG.md` - Change history for this file
- `notes/BUILD_LOG.md` - Detailed build log with decisions

---

## Quick Reference

**Start the app**:
```bash
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

**Run tests**:
```bash
cd backend && pytest tests/unit/ -v
```

**Key files to understand**:
1. `backend/app/memory/retriever.py` - Query-aware memory
2. `backend/app/agents/graph.py` - LangGraph workflow
3. `backend/app/api/routes/chat.py` - Main chat endpoint
4. `frontend/src/components/Chat.tsx` - Chat UI
