# Build Log

Detailed log of build phases, decisions, and outcomes.

---

## Phase 3: API & Frontend (2026-02-01)

### Objective
Build REST API endpoints and React frontend for the coaching platform.

### Worktrees Used
- `worktree-api` → branch `feature/api-routes`
- `worktree-frontend` → branch `feature/frontend`

### API Routes Implemented

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat` | POST | Multi-agent chat with safety checks |
| `/api/voice/transcribe` | POST | Whisper audio transcription |
| `/api/image/analyze` | POST | Claude Vision food analysis |
| `/api/profile/{user_id}` | GET | Get user profile |
| `/api/profile/{user_id}` | POST | Create user profile |
| `/api/profile/{user_id}` | PUT | Update user profile |
| `/api/profile/{user_id}` | DELETE | Delete user profile (GDPR) |
| `/api/profile/{user_id}/injury` | POST | Add injury to profile |

### Frontend Components

| Component | Purpose |
|-----------|---------|
| `Chat.tsx` | Main chat interface with message history |
| `VoiceInput.tsx` | Microphone recording with visual feedback |
| `ImageUpload.tsx` | Food photo upload with analysis preview |
| `useChat.ts` | Chat state management hook |
| `useVoice.ts` | Voice recording hook |
| `api.ts` | Backend API client |

### Test Results
- API tests: 14/14 passing
- Total unit tests: 150+ passing

### Issues Encountered
1. **Pydantic field name conflict**: `date` field clashed with `datetime.date` type
   - **Fix**: Renamed to `record_date` in ShortTermMemory schema
2. **Missing type import**: `any` vs `Any` in MemoryUpdate schema
   - **Fix**: Changed to `Any` from typing module

### Merge Status
- `feature/api-routes` → merged to main (fast-forward)
- `feature/frontend` → merged to main (merge commit)

---

## Phase 2: Tools, Input, Agents (2026-02-01)

### Objective
Build business logic modules for agent tools, input processing, and orchestration.

### Modules Built

**Tools Module:**
- `food_db.py` - USDA FoodData Central API integration
- `exercise_db.py` - wger.de exercise database
- `calculators.py` - BMR, TDEE, macro calculations

**Input Module:**
- `voice.py` - Whisper API speech-to-text
- `image.py` - Claude Vision food image analysis
- `text.py` - Query preprocessing and safety checks

**Agents Module:**
- `state.py` - AgentState TypedDict for LangGraph
- `router.py` - Intent classification and agent routing
- `base.py` - BaseAgent abstract class
- `trainer.py` - Fitness agent with injury awareness
- `nutritionist.py` - Nutrition agent
- `recovery.py` - Sleep/recovery coach
- `graph.py` - LangGraph workflow orchestration

### Test Results
- Tools: 10/10 passing
- Input: 10/10 passing
- Agents: 10/10 passing

---

## Phase 1: Memory, Retrieval, Ingestion (2026-02-01)

### Objective
Build core infrastructure for memory management and RAG pipeline.

### Modules Built

**Memory Module:**
- `schemas.py` - Pydantic models for all memory tiers
- `working.py` - Redis/fallback session state
- `short_term.py` - SQLite 7-day rolling memory
- `long_term.py` - SQLite permanent profile
- `retriever.py` - Query-aware memory fetching

**Retrieval Module:**
- `embedder.py` - sentence-transformers integration
- `vectorstore.py` - ChromaDB operations
- `search.py` - Hybrid search with web fallback

**Ingestion Module:**
- `loader.py` - PDF/text document loading
- `chunker.py` - Semantic text chunking

### Test Results
- Memory: 20/20 passing
- Retrieval: 10/10 passing
- Ingestion: 10/10 passing

---

## Architecture Decisions Log

### Decision 1: Three-Tier Memory
**Context**: Need to balance conversation context with token limits
**Decision**: Separate working (session), short-term (7-day), long-term (permanent)
**Rationale**: Query-aware retrieval reduces token waste

### Decision 2: No Fine-tuning
**Context**: User wants personalization without model training
**Decision**: RAG + tool calling + prompt injection
**Rationale**: Maintains flexibility, reduces cost, allows real-time data

### Decision 3: LangGraph for Agents
**Context**: Need multi-agent coordination with state management
**Decision**: Use LangGraph StateGraph over LangChain agents
**Rationale**: Better control flow, easier debugging, explicit state

### Decision 4: Redis with Fallback
**Context**: Redis may not be available in all environments
**Decision**: In-memory dict fallback when Redis unavailable
**Rationale**: Graceful degradation for development/testing
