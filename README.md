# Adaptive Adolescent Coaching Platform (AACP)

A multi-agent RAG (Retrieval-Augmented Generation) application providing holistic health coaching for adolescents aged 16-19. The platform offers personalized guidance on nutrition, fitness, and recovery through an intelligent conversational interface.

## Features

- **Multi-Agent Architecture**: LangGraph-powered agents specialized in training, nutrition, and recovery
- **Three-Tier Memory System**: Working (session), Short-term (7-day), and Long-term (permanent) memory stores
- **Query-Aware Retrieval**: Intelligent context fetching based on query intent
- **Multi-Modal Input**: Support for text, voice (Whisper), and image (Claude Vision) inputs
- **Safety Guardrails**: Built-in content moderation for adolescent-appropriate responses
- **Real-Time Data**: Integration with USDA FoodData Central and exercise databases

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React + Next.js 14, Tailwind CSS |
| Backend | Python + FastAPI |
| Agent Orchestration | LangGraph |
| LLM | Claude Sonnet 4 |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Store | ChromaDB |
| Database | SQLite |
| Cache | Redis (with in-memory fallback) |
| Speech-to-Text | OpenAI Whisper |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── core/           # Config, utilities
│   │   ├── memory/         # Three-tier memory system
│   │   ├── retrieval/      # RAG pipeline (embed, search)
│   │   ├── ingestion/      # Document loading, chunking
│   │   ├── tools/          # Agent tools (food DB, exercise DB)
│   │   ├── input/          # Voice, image, text processing
│   │   ├── agents/         # LangGraph agents
│   │   └── api/            # FastAPI routes
│   └── tests/
│       ├── unit/           # Unit tests (84+ tests)
│       ├── integration/    # Cross-module tests (19 tests)
│       └── e2e/            # End-to-end tests (7 tests)
├── frontend/
│   └── src/
│       ├── app/            # Next.js pages
│       ├── components/     # Chat, VoiceInput, ImageUpload
│       ├── hooks/          # useChat, useVoice
│       └── lib/            # API client
├── PRD.md                  # Product requirements
├── SYSTEM_DESIGN.md        # Technical design
└── CLAUDE.md               # Project context for AI assistants
```

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- Redis (optional, falls back to in-memory)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here  # For Whisper

# Run the server
uvicorn app.main:app --reload --port 8001
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Multi-agent chat with safety checks |
| `/api/voice/transcribe` | POST | Whisper audio transcription |
| `/api/image/analyze` | POST | Claude Vision food analysis |
| `/api/profile/{user_id}` | GET/POST/PUT/DELETE | User profile CRUD |
| `/api/profile/{user_id}/injury` | POST | Add injury to profile |
| `/health` | GET | Application health check |

## Usage

### Chat Request

```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What workout should I do for building muscle?",
    "user_id": "user123"
  }'
```

### Create User Profile

```bash
curl -X POST http://localhost:8001/api/profile/user123 \
  -H "Content-Type: application/json" \
  -d '{
    "age": 17,
    "height_cm": 175.0,
    "weight_kg": 70.0,
    "dietary_pref": "omnivore",
    "fitness_level": "beginner",
    "primary_goal": "build_muscle"
  }'
```

## Architecture

### Three-Tier Memory System

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

### Multi-Agent Workflow

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

## Testing

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run E2E tests
pytest tests/e2e/ -v

# Run with coverage
pytest --cov=app tests/
```

**Test Summary**: 176 tests passing (unit + integration + e2e)

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | - | Claude API key |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key (for Whisper) |
| `REDIS_HOST` | No | localhost | Redis server host |
| `REDIS_PORT` | No | 6379 | Redis server port |
| `DEBUG` | No | false | Enable debug logging |
| `API_PORT` | No | 8000 | API server port |

## Safety Features

- Content moderation for harmful diet/exercise queries
- Age-appropriate response filtering
- Input validation and sanitization
- Rate limiting on external API calls

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is part of an interview submission.

## Acknowledgments

- Built with Claude Code by Anthropic
- Uses free APIs from USDA FoodData Central and wger.de
