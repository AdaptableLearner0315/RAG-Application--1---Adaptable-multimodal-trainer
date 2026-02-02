# CLAUDE.md - Project Context for AI Assistants

## Project Overview

**Adaptive Adolescent Coaching Platform (AACP)** - A multi-agent RAG application providing holistic health coaching (nutrition, fitness, recovery) for adolescents aged 16-19.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React + Next.js 14 |
| Backend | Python + FastAPI |
| Agent Orchestration | LangGraph |
| LLM | Claude Sonnet 4 |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Store | ChromaDB |
| Database | SQLite |
| Cache | Redis (with in-memory fallback) |
| Speech-to-Text | Whisper API |
| Observability | Langfuse |
| Testing | pytest (backend), Jest (frontend) |

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
│   │   └── api/            # ⏳ FastAPI routes
│   └── tests/
│       ├── unit/           # Unit tests per module
│       ├── integration/    # Cross-module tests (pending)
│       └── e2e/            # End-to-end tests (pending)
├── frontend/               # ⏳ Next.js app
├── PRD.md                  # Product requirements
└── SYSTEM_DESIGN.md        # Technical design
```

## Build Status

| Module | Status | Tests |
|--------|--------|-------|
| Memory | ✅ Complete | 20 tests |
| Retrieval | ✅ Complete | 10 tests |
| Ingestion | ✅ Complete | 10 tests |
| Tools | ✅ Complete | 10 tests |
| Input | ✅ Complete | 10 tests |
| Agents | ✅ Complete | 10 tests |
| API Routes | ⏳ Pending | - |
| Frontend | ⏳ Pending | - |

## Key Architecture Decisions

### 1. Three-Tier Memory System
- **Working Memory**: Redis/session state for current conversation
- **Short-term Memory**: SQLite, 7-day rolling window for recent activity
- **Long-term Memory**: SQLite, permanent user profile

### 2. Query-Aware Memory Retrieval
Memory retriever analyzes query intent and fetches only relevant context:
- Workout query → injuries, recent workouts, fitness level
- Food query → intolerances, recent meals, dietary preferences
- Sleep query → sleep logs, recent workouts

### 3. Multi-Agent Architecture (LangGraph)
Three specialized agents sharing user context:
- **Trainer Agent**: Fitness, exercises, injury modifications
- **Nutritionist Agent**: Meals, macros, food image analysis
- **Recovery Coach**: Sleep, rest days, recovery protocols

### 4. No Fine-tuning
All personalization via:
- RAG retrieval from knowledge base
- Tool calling for real-time data (USDA, exercise DBs)
- Prompt injection with user memory context

## Development Patterns

### Module Structure
Each module follows single-responsibility:
```python
# One class per file, <100 lines
# Docstrings on every function
# Type hints throughout
```

### Testing Strategy
- 5 edge cases per component
- Unit tests first, then integration
- Test file mirrors source structure

### Git Workflow
- Feature branches per module
- Worktrees for parallel development
- Merge to main only after tests pass

## Commands

```bash
# Run tests
cd backend && pytest tests/unit/ -v

# Run specific module tests
pytest tests/unit/test_memory/ -v

# Run with coverage
pytest --cov=app tests/
```

## Environment Variables

```bash
ANTHROPIC_API_KEY=     # Required for Claude
OPENAI_API_KEY=        # Required for Whisper
REDIS_HOST=localhost   # Optional, falls back to in-memory
DEBUG=false            # Enable debug logging
```

## Free APIs Used

| API | Purpose | Docs |
|-----|---------|------|
| USDA FoodData Central | Nutrition lookup | https://fdc.nal.usda.gov/api-guide.html |
| wger.de | Exercise database | https://wger.de/en/software/api |
| DuckDuckGo Search | Web fallback | duckduckgo-search package |

## Current Sprint

Building Phase 3 - API & UI:
1. **API Routes** - FastAPI endpoints for chat, voice, image, profile
2. **Frontend** - Next.js app with React components

## Completed Phases

- **Phase 1**: Core Infrastructure (Memory, Retrieval, Ingestion)
- **Phase 2**: Business Logic (Tools, Input, Agents)
