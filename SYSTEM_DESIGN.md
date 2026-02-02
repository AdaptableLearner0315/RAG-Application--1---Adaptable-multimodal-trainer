# System Design: Adaptive Adolescent Coaching Platform

**Design Principles:**
1. Minimal code - single responsibility per function
2. Super modular - each module is independent, swappable
3. Docstrings everywhere - every function documented
4. Memory-first architecture - query-aware context injection
5. Test-driven - unit tests before integration

---

## 1. Tech Stack

### 1.1 Overview

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React + Next.js | Web UI with SSR |
| **Backend** | Python (FastAPI) | REST API server |
| **Agent Orchestration** | LangGraph | Multi-agent workflow |
| **LLM** | Claude Sonnet 4 | Reasoning + Vision |
| **Embeddings** | sentence-transformers | Local embeddings (free) |
| **Vector Store** | ChromaDB | Local vector DB (free) |
| **Database** | SQLite | Memory persistence (free) |
| **Speech-to-Text** | Whisper API | Voice transcription |
| **Observability** | Langfuse (self-hosted) | Tracing (free alternative to LangSmith) |
| **Testing** | pytest + Jest | Backend + Frontend tests |
| **Cache** | Redis | Session + response cache |

### 1.2 Frontend (Next.js)

```
frontend/
├── src/
│   ├── app/                    # Next.js 14 app router
│   │   ├── page.tsx            # Home/chat page
│   │   ├── onboarding/         # User onboarding flow
│   │   └── api/                # API routes (BFF pattern)
│   ├── components/
│   │   ├── Chat.tsx            # Main chat interface
│   │   ├── VoiceInput.tsx      # Mic button + recording
│   │   ├── ImageUpload.tsx     # Food photo upload
│   │   └── AgentAvatar.tsx     # Agent identity display
│   ├── hooks/
│   │   ├── useChat.ts          # Chat state management
│   │   └── useVoice.ts         # Voice recording logic
│   └── lib/
│       └── api.ts              # Backend API client
├── package.json
└── next.config.js
```

### 1.3 Backend (Python + FastAPI)

```
backend/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py         # POST /chat
│   │   │   ├── voice.py        # POST /voice/transcribe
│   │   │   ├── image.py        # POST /image/analyze
│   │   │   └── profile.py      # GET/PUT /profile
│   │   └── deps.py             # Dependency injection
│   ├── core/
│   │   ├── config.py           # Settings
│   │   └── context.py          # Context assembly
│   ├── agents/                 # LangGraph agents
│   │   ├── graph.py            # Main agent graph
│   │   ├── nodes/
│   │   │   ├── router.py       # Query router node
│   │   │   ├── trainer.py      # Trainer agent node
│   │   │   ├── nutritionist.py # Nutritionist node
│   │   │   └── recovery.py     # Recovery coach node
│   │   └── tools/              # Agent tools
│   ├── memory/                 # Memory management
│   │   ├── working.py          # Redis session state
│   │   ├── short_term.py       # SQLite 7-day
│   │   └── long_term.py        # SQLite permanent
│   ├── retrieval/              # RAG components
│   │   ├── embedder.py
│   │   ├── vectorstore.py
│   │   └── search.py
│   └── input/                  # Input processors
│       ├── voice.py
│       └── image.py
├── tests/                      # pytest tests
├── requirements.txt
└── Dockerfile
```

### 1.4 Free/Open-Source Tools

| Need | Tool | Cost |
|------|------|------|
| Observability | **Langfuse** (self-hosted) | Free |
| Vector DB | **ChromaDB** | Free |
| Embeddings | **all-MiniLM-L6-v2** | Free (local) |
| Food data | **USDA FoodData Central API** | Free |
| Exercise data | **wger.de API** | Free |
| Cache | **Redis** (local) | Free |

### 1.5 API Contract (Frontend ↔ Backend)

```typescript
// POST /api/chat
Request: {
  message: string;
  user_id: string;
  image_base64?: string;  // Optional food image
}

Response: {
  response: string;
  agent: "trainer" | "nutritionist" | "recovery";
  sources?: string[];     // RAG sources used
  memory_updated?: boolean;
}

// POST /api/voice/transcribe
Request: {
  audio_base64: string;
  format: "webm" | "mp3" | "wav";
}

Response: {
  text: string;
  confidence: number;
}

// GET /api/profile/{user_id}
Response: {
  age: number;
  weight_kg: number;
  height_cm: number;
  injuries: string[];
  intolerances: string[];
  goals: string;
}
```

---

## 2. Project Structure

```
project/
├── frontend/                   # Next.js app
│   ├── src/
│   ├── package.json
│   └── Dockerfile
│
├── backend/                    # Python FastAPI
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml          # Local dev orchestration
├── PRD.md                      # Product requirements
└── SYSTEM_DESIGN.md            # This document
```

---

## 3. Module Structure (Backend Detail)

```
backend/app/
├── main.py                # FastAPI entry point
├── core/
│   ├── config.py          # Centralized configuration
│   └── context.py         # Context assembly for LLM
│
├── agents/                # LangGraph orchestration
│   ├── graph.py           # StateGraph definition
│   ├── state.py           # Agent state schema
│   └── nodes/
│       ├── router.py      # Intent classification
│       ├── trainer.py     # Fitness agent
│       ├── nutritionist.py# Nutrition agent
│       └── recovery.py    # Recovery agent
│
├── memory/                # Three-tier memory
│   ├── working.py         # Redis (session)
│   ├── short_term.py      # SQLite (7-day)
│   ├── long_term.py       # SQLite (permanent)
│   └── retriever.py       # Query-aware fetch
│
├── retrieval/             # RAG pipeline
│   ├── embedder.py        # sentence-transformers
│   ├── vectorstore.py     # ChromaDB
│   └── search.py          # Hybrid search
│
├── tools/                 # Agent tools
│   ├── food_db.py         # USDA API
│   ├── exercise_db.py     # wger API
│   └── calculators.py     # Macro calculations
│
└── input/                 # Input processing
    ├── voice.py           # Whisper STT
    └── image.py           # Claude Vision
```

---

## 2. Memory Architecture (Critical Path)

### 2.1 Three-Tier Memory Model

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER QUERY ARRIVES                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY RETRIEVER                             │
│                                                                 │
│  1. Analyze query intent                                        │
│  2. Determine which memory tiers are relevant                   │
│  3. Fetch only what's needed                                    │
│  4. Compress into token budget                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   WORKING     │     │  SHORT-TERM   │     │   LONG-TERM   │
│   MEMORY      │     │    MEMORY     │     │    MEMORY     │
├───────────────┤     ├───────────────┤     ├───────────────┤
│ Storage:      │     │ Storage:      │     │ Storage:      │
│ Session state │     │ SQLite        │     │ SQLite        │
│ (in-memory)   │     │ (rolling 7d)  │     │ (permanent)   │
├───────────────┤     ├───────────────┤     ├───────────────┤
│ Contains:     │     │ Contains:     │     │ Contains:     │
│ • Last 5 msgs │     │ • Meal logs   │     │ • Profile     │
│ • Current ctx │     │ • Workout logs│     │ • Injuries    │
│ • Active goal │     │ • Sleep logs  │     │ • Preferences │
│               │     │ • Adherence % │     │ • Goals       │
├───────────────┤     ├───────────────┤     ├───────────────┤
│ Token budget: │     │ Token budget: │     │ Token budget: │
│ 500 tokens    │     │ 800 tokens    │     │ 400 tokens    │
└───────────────┘     └───────────────┘     └───────────────┘
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CONTEXT ASSEMBLY                              │
│                                                                 │
│  System Prompt (500 tokens)                                     │
│  + Long-term Memory (400 tokens) ← Profile, injuries, goals     │
│  + Short-term Memory (800 tokens) ← Recent relevant activity    │
│  + Working Memory (500 tokens) ← Current conversation           │
│  + Retrieved RAG docs (1500 tokens)                             │
│  + User Query (200 tokens)                                      │
│  ─────────────────────────────────────                          │
│  = Total Context: ~3900 tokens (leaves room for response)       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM CALL                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Query-Aware Memory Retrieval

**Key insight**: Not all queries need all memory. Fetch only relevant context.

```python
# memory/retriever.py

QUERY_MEMORY_MAP = {
    # Query pattern → Memory sections needed
    "workout|exercise|training": {
        "long_term": ["injuries", "fitness_level", "goals"],
        "short_term": ["recent_workouts", "fatigue_signals"],
        "working": ["last_3_messages"]
    },
    "food|meal|eat|nutrition|calories": {
        "long_term": ["intolerances", "allergies", "dietary_pref", "goals"],
        "short_term": ["recent_meals", "calorie_balance"],
        "working": ["last_3_messages"]
    },
    "sleep|tired|rest|recovery": {
        "long_term": ["sleep_preferences", "goals"],
        "short_term": ["sleep_logs", "recent_workouts"],
        "working": ["last_3_messages"]
    },
    "plan|week|schedule": {
        "long_term": ["full_profile"],
        "short_term": ["full_week_data", "adherence"],
        "working": ["last_5_messages"]
    }
}
```

### 2.3 Memory Schemas (Minimal)

```python
# memory/schemas.py

@dataclass
class LongTermMemory:
    """Permanent user profile. Updated rarely."""
    user_id: str
    created_at: datetime

    # Core demographics (set once)
    age: int
    height_cm: float
    weight_kg: float

    # Health constraints (updated when user reports)
    injuries: List[str]           # ["left knee ACL", "lower back"]
    intolerances: List[str]       # ["lactose", "gluten"]
    allergies: List[str]          # ["peanuts"]

    # Preferences (learned over time)
    dietary_pref: str             # "omnivore" | "vegetarian" | "vegan"
    fitness_level: str            # "beginner" | "intermediate" | "advanced"

    # Goals (user-set, can change)
    primary_goal: str             # "build_muscle" | "lose_fat" | "maintain"
    target_weight_kg: Optional[float]


@dataclass
class ShortTermMemory:
    """Rolling 7-day activity window. Auto-expires."""
    user_id: str
    date: date

    # Daily logs
    meals: List[Dict]             # [{time, foods, calories, protein, carbs, fat}]
    workouts: List[Dict]          # [{time, type, duration_min, intensity}]
    sleep: Optional[Dict]         # {bed_time, wake_time, quality_1_5}

    # Derived metrics
    calories_consumed: int
    calories_burned: int
    protein_total: int


@dataclass
class WorkingMemory:
    """Current session only. Cleared on exit."""
    conversation: List[Dict]      # [{role, content, timestamp}]
    current_agent: Optional[str]  # Which agent is active
    pending_context: Dict         # Retrieved docs, tool results
```

### 2.4 Memory Retriever Implementation

```python
# memory/retriever.py

class MemoryRetriever:
    """
    Query-aware memory fetching.
    Retrieves only relevant memory sections based on query intent.
    """

    def __init__(
        self,
        working: WorkingMemoryStore,
        short_term: ShortTermMemoryStore,
        long_term: LongTermMemoryStore,
        token_budgets: Dict[str, int]
    ):
        """
        Initialize memory retriever with all three memory stores.

        Args:
            working: Session-scoped memory store
            short_term: 7-day rolling memory store
            long_term: Permanent profile store
            token_budgets: Max tokens per memory tier
        """
        self.working = working
        self.short_term = short_term
        self.long_term = long_term
        self.budgets = token_budgets

    def retrieve_for_query(
        self,
        user_id: str,
        query: str
    ) -> Dict[str, str]:
        """
        Retrieve relevant memory context for a given query.

        Args:
            user_id: User identifier
            query: Raw user query text

        Returns:
            Dict with keys 'long_term', 'short_term', 'working'
            Each value is a formatted string within token budget
        """
        intent = self._classify_intent(query)
        memory_spec = QUERY_MEMORY_MAP.get(intent, DEFAULT_MEMORY_SPEC)

        context = {}

        # Fetch long-term (always needed, but subset varies)
        lt_fields = memory_spec["long_term"]
        context["long_term"] = self._fetch_long_term(user_id, lt_fields)

        # Fetch short-term (query-dependent)
        st_fields = memory_spec["short_term"]
        context["short_term"] = self._fetch_short_term(user_id, st_fields)

        # Fetch working (recent conversation)
        msg_count = memory_spec["working"].get("message_count", 3)
        context["working"] = self._fetch_working(msg_count)

        return context

    def _classify_intent(self, query: str) -> str:
        """
        Classify query intent using keyword matching.

        Args:
            query: Raw query text

        Returns:
            Intent category string
        """
        query_lower = query.lower()

        for pattern, _ in QUERY_MEMORY_MAP.items():
            if any(kw in query_lower for kw in pattern.split("|")):
                return pattern

        return "general"

    def _fetch_long_term(
        self,
        user_id: str,
        fields: List[str]
    ) -> str:
        """
        Fetch and format long-term memory fields.

        Args:
            user_id: User identifier
            fields: List of profile fields to include

        Returns:
            Formatted string within token budget
        """
        profile = self.long_term.get(user_id)
        if not profile:
            return ""

        selected = {f: getattr(profile, f) for f in fields if hasattr(profile, f)}
        formatted = self._format_memory(selected, self.budgets["long_term"])
        return formatted

    def _fetch_short_term(
        self,
        user_id: str,
        fields: List[str]
    ) -> str:
        """
        Fetch and format short-term memory fields.

        Args:
            user_id: User identifier
            fields: List of activity fields to include

        Returns:
            Formatted string within token budget
        """
        recent = self.short_term.get_recent(user_id, days=7)
        if not recent:
            return ""

        selected = {}
        for field in fields:
            if field == "recent_meals":
                selected["meals"] = self._summarize_meals(recent)
            elif field == "recent_workouts":
                selected["workouts"] = self._summarize_workouts(recent)
            elif field == "sleep_logs":
                selected["sleep"] = self._summarize_sleep(recent)

        formatted = self._format_memory(selected, self.budgets["short_term"])
        return formatted

    def _fetch_working(self, message_count: int) -> str:
        """
        Fetch recent conversation from working memory.

        Args:
            message_count: Number of recent messages to include

        Returns:
            Formatted conversation string within token budget
        """
        messages = self.working.get_recent(message_count)
        formatted = self._format_conversation(messages, self.budgets["working"])
        return formatted

    def _format_memory(self, data: Dict, max_tokens: int) -> str:
        """
        Format memory dict as string, truncating to fit budget.

        Args:
            data: Memory data dictionary
            max_tokens: Maximum token count

        Returns:
            Formatted string within budget
        """
        # Simple formatting - can be enhanced
        lines = [f"{k}: {v}" for k, v in data.items() if v]
        text = "\n".join(lines)
        return self._truncate_to_tokens(text, max_tokens)

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to approximate token count.

        Args:
            text: Input text
            max_tokens: Maximum tokens (approx 4 chars/token)

        Returns:
            Truncated text
        """
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars-3] + "..."
```

---

## 3. Module Designs with Edge Cases & Unit Tests

### 3.1 Ingestion Module

**Files**: `loader.py`, `chunker.py`
**Purpose**: Load documents, split into semantic chunks

```python
# ingestion/loader.py

class DocumentLoader:
    """Load and extract text from PDF documents."""

    def load(self, file_path: Path) -> str:
        """
        Load text content from a PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text content

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or unreadable
        """
        pass
```

**Edge Cases (5):**

| # | Edge Case | Expected Behavior |
|---|-----------|-------------------|
| 1 | PDF file not found | Raise `FileNotFoundError` with clear message |
| 2 | PDF is corrupted/unreadable | Raise `ValueError("Cannot extract text from PDF")` |
| 3 | PDF has no extractable text (scanned) | Return empty string, log warning |
| 4 | PDF exceeds size limit (>50MB) | Raise `ValueError("File exceeds 50MB limit")` |
| 5 | PDF path contains special characters | Handle unicode paths correctly |

**Unit Tests:**

```python
# tests/unit/test_ingestion/test_loader.py

import pytest
from pathlib import Path
from src.ingestion.loader import DocumentLoader


class TestDocumentLoader:
    """Unit tests for DocumentLoader class."""

    @pytest.fixture
    def loader(self):
        """Create DocumentLoader instance."""
        return DocumentLoader()

    # Edge Case 1: File not found
    def test_load_nonexistent_file_raises_error(self, loader):
        """
        GIVEN a path to a nonexistent file
        WHEN load() is called
        THEN FileNotFoundError is raised
        """
        fake_path = Path("/nonexistent/file.pdf")

        with pytest.raises(FileNotFoundError) as exc_info:
            loader.load(fake_path)

        assert "not found" in str(exc_info.value).lower()

    # Edge Case 2: Corrupted PDF
    def test_load_corrupted_pdf_raises_error(self, loader, tmp_path):
        """
        GIVEN a corrupted PDF file
        WHEN load() is called
        THEN ValueError is raised with descriptive message
        """
        corrupted = tmp_path / "corrupted.pdf"
        corrupted.write_bytes(b"not a real pdf content")

        with pytest.raises(ValueError) as exc_info:
            loader.load(corrupted)

        assert "cannot extract" in str(exc_info.value).lower()

    # Edge Case 3: Scanned PDF (no text)
    def test_load_scanned_pdf_returns_empty(self, loader, scanned_pdf_fixture):
        """
        GIVEN a scanned PDF with no extractable text
        WHEN load() is called
        THEN empty string is returned
        """
        result = loader.load(scanned_pdf_fixture)

        assert result == ""

    # Edge Case 4: Oversized PDF
    def test_load_oversized_pdf_raises_error(self, loader, tmp_path):
        """
        GIVEN a PDF exceeding 50MB
        WHEN load() is called
        THEN ValueError is raised
        """
        large_file = tmp_path / "large.pdf"
        # Create file > 50MB (mock or actual)
        large_file.write_bytes(b"0" * (51 * 1024 * 1024))

        with pytest.raises(ValueError) as exc_info:
            loader.load(large_file)

        assert "50mb" in str(exc_info.value).lower()

    # Edge Case 5: Unicode path
    def test_load_unicode_path_works(self, loader, tmp_path, valid_pdf_content):
        """
        GIVEN a PDF with unicode characters in path
        WHEN load() is called
        THEN text is extracted successfully
        """
        unicode_path = tmp_path / "документ_日本語.pdf"
        unicode_path.write_bytes(valid_pdf_content)

        result = loader.load(unicode_path)

        assert isinstance(result, str)
```

```python
# ingestion/chunker.py

class SemanticChunker:
    """Split text into semantic chunks for embedding."""

    def chunk(self, text: str) -> List[str]:
        """
        Split text into semantically coherent chunks.

        Args:
            text: Raw text to chunk

        Returns:
            List of text chunks within size limits
        """
        pass
```

**Edge Cases (5):**

| # | Edge Case | Expected Behavior |
|---|-----------|-------------------|
| 1 | Empty text input | Return empty list |
| 2 | Text shorter than min_chunk_size | Return single chunk with full text |
| 3 | Text with no natural break points | Force split at max_chunk_size |
| 4 | Text with only whitespace | Return empty list |
| 5 | Very long single paragraph | Split mid-sentence at max size |

**Unit Tests:**

```python
# tests/unit/test_ingestion/test_chunker.py

import pytest
from src.ingestion.chunker import SemanticChunker


class TestSemanticChunker:
    """Unit tests for SemanticChunker class."""

    @pytest.fixture
    def chunker(self):
        """Create SemanticChunker with default config."""
        return SemanticChunker(
            min_chunk_size=200,
            max_chunk_size=800,
            overlap=50
        )

    # Edge Case 1: Empty input
    def test_chunk_empty_text_returns_empty_list(self, chunker):
        """
        GIVEN empty string input
        WHEN chunk() is called
        THEN empty list is returned
        """
        result = chunker.chunk("")

        assert result == []

    # Edge Case 2: Short text
    def test_chunk_short_text_returns_single_chunk(self, chunker):
        """
        GIVEN text shorter than min_chunk_size
        WHEN chunk() is called
        THEN single chunk with full text is returned
        """
        short_text = "This is a short text."

        result = chunker.chunk(short_text)

        assert len(result) == 1
        assert result[0] == short_text

    # Edge Case 3: No natural breaks
    def test_chunk_no_breaks_forces_split(self, chunker):
        """
        GIVEN text with no sentence/paragraph breaks
        WHEN chunk() is called
        THEN text is split at max_chunk_size boundary
        """
        continuous_text = "word " * 500  # ~2500 chars, no breaks

        result = chunker.chunk(continuous_text)

        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= chunker.max_chunk_size * 4  # approx chars

    # Edge Case 4: Whitespace only
    def test_chunk_whitespace_returns_empty_list(self, chunker):
        """
        GIVEN text with only whitespace
        WHEN chunk() is called
        THEN empty list is returned
        """
        whitespace = "   \n\t\n   "

        result = chunker.chunk(whitespace)

        assert result == []

    # Edge Case 5: Long paragraph
    def test_chunk_long_paragraph_splits_correctly(self, chunker):
        """
        GIVEN single paragraph exceeding max_chunk_size
        WHEN chunk() is called
        THEN paragraph is split with overlap preserved
        """
        long_para = "This is a sentence. " * 100  # Long single paragraph

        result = chunker.chunk(long_para)

        assert len(result) > 1
        # Verify overlap exists between consecutive chunks
        for i in range(len(result) - 1):
            chunk_end = result[i][-100:]  # Last 100 chars
            chunk_start = result[i + 1][:100]  # First 100 chars
            # Some overlap should exist
            assert any(word in chunk_start for word in chunk_end.split()[-5:])
```

---

### 3.2 Retrieval Module

**Files**: `vectorstore.py`, `embedder.py`, `search.py`
**Purpose**: Embed queries, search vector store, hybrid search

```python
# retrieval/embedder.py

class Embedder:
    """Generate embeddings for text using sentence-transformers."""

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding vector for input text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        pass

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass
```

**Edge Cases (5):**

| # | Edge Case | Expected Behavior |
|---|-----------|-------------------|
| 1 | Empty string input | Return zero vector or raise ValueError |
| 2 | Text exceeds model max length (512 tokens) | Truncate with warning |
| 3 | Batch with mixed empty/valid texts | Skip empty, embed valid, maintain order |
| 4 | Model not loaded/available | Raise clear error with model name |
| 5 | Unicode/emoji in text | Handle gracefully, embed successfully |

**Unit Tests:**

```python
# tests/unit/test_retrieval/test_embedder.py

import pytest
from src.retrieval.embedder import Embedder


class TestEmbedder:
    """Unit tests for Embedder class."""

    @pytest.fixture
    def embedder(self):
        """Create Embedder with test model."""
        return Embedder(model_name="all-MiniLM-L6-v2")

    # Edge Case 1: Empty input
    def test_embed_empty_string_raises_error(self, embedder):
        """
        GIVEN empty string
        WHEN embed() is called
        THEN ValueError is raised
        """
        with pytest.raises(ValueError) as exc_info:
            embedder.embed("")

        assert "empty" in str(exc_info.value).lower()

    # Edge Case 2: Oversized text
    def test_embed_long_text_truncates(self, embedder):
        """
        GIVEN text exceeding 512 tokens
        WHEN embed() is called
        THEN text is truncated and embedding returned
        """
        long_text = "word " * 1000  # Way over 512 tokens

        result = embedder.embed(long_text)

        assert isinstance(result, list)
        assert len(result) == 384  # MiniLM dimension

    # Edge Case 3: Batch with empty strings
    def test_embed_batch_handles_empty_strings(self, embedder):
        """
        GIVEN batch with some empty strings
        WHEN embed_batch() is called
        THEN empty strings get zero vectors, order preserved
        """
        texts = ["valid text", "", "another valid"]

        result = embedder.embed_batch(texts)

        assert len(result) == 3
        assert all(v == 0.0 for v in result[1])  # Empty gets zeros
        assert not all(v == 0.0 for v in result[0])  # Valid gets real embedding

    # Edge Case 4: Model not available
    def test_embed_missing_model_raises_error(self):
        """
        GIVEN invalid model name
        WHEN Embedder is initialized
        THEN clear error is raised
        """
        with pytest.raises(ValueError) as exc_info:
            Embedder(model_name="nonexistent-model-xyz")

        assert "model" in str(exc_info.value).lower()

    # Edge Case 5: Unicode content
    def test_embed_unicode_text_works(self, embedder):
        """
        GIVEN text with unicode/emoji
        WHEN embed() is called
        THEN embedding is generated successfully
        """
        unicode_text = "Здравствуйте! 你好 🍎🥗"

        result = embedder.embed(unicode_text)

        assert isinstance(result, list)
        assert len(result) == 384
```

```python
# retrieval/search.py

class HybridSearcher:
    """Combine vector search with web search fallback."""

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        Search for relevant documents using hybrid approach.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of SearchResult objects ranked by relevance
        """
        pass
```

**Edge Cases (5):**

| # | Edge Case | Expected Behavior |
|---|-----------|-------------------|
| 1 | Vector search returns 0 results | Fall back to web search |
| 2 | Both vector and web return 0 results | Return empty list with log |
| 3 | Web search times out | Return vector results only |
| 4 | Query is single character | Expand or reject with message |
| 5 | Results all below similarity threshold | Return best match with confidence warning |

**Unit Tests:**

```python
# tests/unit/test_retrieval/test_search.py

import pytest
from unittest.mock import Mock, patch
from src.retrieval.search import HybridSearcher


class TestHybridSearcher:
    """Unit tests for HybridSearcher class."""

    @pytest.fixture
    def searcher(self, mock_vectorstore, mock_websearch):
        """Create HybridSearcher with mocked dependencies."""
        return HybridSearcher(
            vectorstore=mock_vectorstore,
            websearch=mock_websearch,
            similarity_threshold=0.5
        )

    # Edge Case 1: Vector empty, web fallback
    def test_search_falls_back_to_web_on_empty_vector(
        self, searcher, mock_vectorstore, mock_websearch
    ):
        """
        GIVEN vector search returns empty
        WHEN search() is called
        THEN web search is used as fallback
        """
        mock_vectorstore.search.return_value = []
        mock_websearch.search.return_value = [Mock(content="web result")]

        result = searcher.search("nutrition tips")

        assert len(result) > 0
        mock_websearch.search.assert_called_once()

    # Edge Case 2: Both return empty
    def test_search_returns_empty_when_all_fail(
        self, searcher, mock_vectorstore, mock_websearch
    ):
        """
        GIVEN both vector and web search return empty
        WHEN search() is called
        THEN empty list is returned
        """
        mock_vectorstore.search.return_value = []
        mock_websearch.search.return_value = []

        result = searcher.search("extremely obscure query xyz123")

        assert result == []

    # Edge Case 3: Web timeout
    def test_search_returns_vector_on_web_timeout(
        self, searcher, mock_vectorstore, mock_websearch
    ):
        """
        GIVEN web search times out
        WHEN search() is called
        THEN vector results are returned
        """
        mock_vectorstore.search.return_value = [Mock(content="vector result")]
        mock_websearch.search.side_effect = TimeoutError()

        result = searcher.search("protein intake")

        assert len(result) == 1
        assert result[0].content == "vector result"

    # Edge Case 4: Single character query
    def test_search_rejects_single_char_query(self, searcher):
        """
        GIVEN single character query
        WHEN search() is called
        THEN ValueError is raised
        """
        with pytest.raises(ValueError) as exc_info:
            searcher.search("a")

        assert "too short" in str(exc_info.value).lower()

    # Edge Case 5: All results below threshold
    def test_search_returns_best_with_warning_when_low_confidence(
        self, searcher, mock_vectorstore
    ):
        """
        GIVEN all results below similarity threshold
        WHEN search() is called
        THEN best result returned with low_confidence flag
        """
        low_score_result = Mock(content="result", score=0.3)
        mock_vectorstore.search.return_value = [low_score_result]

        result = searcher.search("query")

        assert len(result) == 1
        assert result[0].low_confidence is True
```

---

### 3.3 Memory Module (Critical)

**Files**: `working.py`, `short_term.py`, `long_term.py`, `retriever.py`
**Purpose**: Three-tier memory with query-aware retrieval

```python
# memory/long_term.py

class LongTermMemoryStore:
    """Permanent user profile storage using SQLite."""

    def get(self, user_id: str) -> Optional[LongTermMemory]:
        """
        Retrieve user's long-term profile.

        Args:
            user_id: Unique user identifier

        Returns:
            LongTermMemory object or None if not found
        """
        pass

    def upsert(self, user_id: str, data: Dict) -> None:
        """
        Create or update user profile.

        Args:
            user_id: Unique user identifier
            data: Profile data to store/update
        """
        pass

    def add_injury(self, user_id: str, injury: str) -> None:
        """
        Add injury to user's profile.

        Args:
            user_id: Unique user identifier
            injury: Injury description
        """
        pass

    def delete(self, user_id: str) -> bool:
        """
        Delete user profile (GDPR compliance).

        Args:
            user_id: Unique user identifier

        Returns:
            True if deleted, False if not found
        """
        pass
```

**Edge Cases (5):**

| # | Edge Case | Expected Behavior |
|---|-----------|-------------------|
| 1 | User profile not found | Return None, don't raise |
| 2 | Duplicate injury added | Ignore duplicate, don't add twice |
| 3 | Invalid data types in upsert | Validate and raise TypeError |
| 4 | SQLite database locked | Retry with backoff, then raise |
| 5 | Delete nonexistent user | Return False, no error |

**Unit Tests:**

```python
# tests/unit/test_memory/test_long_term.py

import pytest
from src.memory.long_term import LongTermMemoryStore


class TestLongTermMemoryStore:
    """Unit tests for LongTermMemoryStore class."""

    @pytest.fixture
    def store(self, tmp_path):
        """Create LongTermMemoryStore with temp database."""
        db_path = tmp_path / "test_memory.db"
        return LongTermMemoryStore(db_path=db_path)

    @pytest.fixture
    def sample_profile(self):
        """Sample user profile data."""
        return {
            "age": 17,
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "injuries": [],
            "intolerances": ["lactose"],
            "dietary_pref": "omnivore",
            "primary_goal": "build_muscle"
        }

    # Edge Case 1: User not found
    def test_get_nonexistent_user_returns_none(self, store):
        """
        GIVEN user_id that doesn't exist
        WHEN get() is called
        THEN None is returned
        """
        result = store.get("nonexistent_user_123")

        assert result is None

    # Edge Case 2: Duplicate injury
    def test_add_injury_ignores_duplicate(self, store, sample_profile):
        """
        GIVEN user with existing injury
        WHEN same injury is added again
        THEN injury list has no duplicates
        """
        user_id = "user_123"
        store.upsert(user_id, sample_profile)

        store.add_injury(user_id, "left knee")
        store.add_injury(user_id, "left knee")  # Duplicate

        profile = store.get(user_id)
        assert profile.injuries.count("left knee") == 1

    # Edge Case 3: Invalid data type
    def test_upsert_invalid_type_raises_error(self, store):
        """
        GIVEN invalid data type for a field
        WHEN upsert() is called
        THEN TypeError is raised
        """
        invalid_data = {
            "age": "seventeen",  # Should be int
            "height_cm": 175.0
        }

        with pytest.raises(TypeError) as exc_info:
            store.upsert("user_123", invalid_data)

        assert "age" in str(exc_info.value)

    # Edge Case 4: Database locked (simulated)
    def test_upsert_retries_on_db_lock(self, store, sample_profile, mocker):
        """
        GIVEN database is temporarily locked
        WHEN upsert() is called
        THEN operation retries and eventually succeeds
        """
        # Mock to fail twice then succeed
        original_execute = store._execute
        call_count = [0]

        def flaky_execute(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise sqlite3.OperationalError("database is locked")
            return original_execute(*args, **kwargs)

        mocker.patch.object(store, '_execute', side_effect=flaky_execute)

        store.upsert("user_123", sample_profile)

        assert call_count[0] == 3  # Retried twice

    # Edge Case 5: Delete nonexistent
    def test_delete_nonexistent_returns_false(self, store):
        """
        GIVEN user_id that doesn't exist
        WHEN delete() is called
        THEN False is returned, no error
        """
        result = store.delete("nonexistent_user_456")

        assert result is False
```

```python
# memory/short_term.py

class ShortTermMemoryStore:
    """Rolling 7-day activity memory using SQLite."""

    def log_meal(self, user_id: str, meal: Dict) -> None:
        """
        Log a meal to short-term memory.

        Args:
            user_id: Unique user identifier
            meal: Meal data {time, foods, calories, protein, carbs, fat}
        """
        pass

    def log_workout(self, user_id: str, workout: Dict) -> None:
        """
        Log a workout to short-term memory.

        Args:
            user_id: Unique user identifier
            workout: Workout data {time, type, duration_min, intensity}
        """
        pass

    def get_recent(
        self,
        user_id: str,
        days: int = 7
    ) -> List[ShortTermMemory]:
        """
        Get recent activity within rolling window.

        Args:
            user_id: Unique user identifier
            days: Number of days to look back

        Returns:
            List of daily activity records
        """
        pass

    def cleanup_expired(self) -> int:
        """
        Remove records older than retention period.

        Returns:
            Number of records deleted
        """
        pass
```

**Edge Cases (5):**

| # | Edge Case | Expected Behavior |
|---|-----------|-------------------|
| 1 | Log meal with missing required fields | Raise ValueError listing missing fields |
| 2 | Get recent for new user (no data) | Return empty list |
| 3 | Data exactly at 7-day boundary | Include in results (inclusive) |
| 4 | Negative calories/duration in log | Reject with ValueError |
| 5 | Cleanup with no expired data | Return 0, no error |

**Unit Tests:**

```python
# tests/unit/test_memory/test_short_term.py

import pytest
from datetime import date, timedelta
from src.memory.short_term import ShortTermMemoryStore


class TestShortTermMemoryStore:
    """Unit tests for ShortTermMemoryStore class."""

    @pytest.fixture
    def store(self, tmp_path):
        """Create ShortTermMemoryStore with temp database."""
        db_path = tmp_path / "test_short_term.db"
        return ShortTermMemoryStore(db_path=db_path)

    @pytest.fixture
    def valid_meal(self):
        """Valid meal data."""
        return {
            "time": "12:30",
            "foods": ["chicken breast", "rice", "broccoli"],
            "calories": 550,
            "protein": 45,
            "carbs": 60,
            "fat": 12
        }

    # Edge Case 1: Missing required fields
    def test_log_meal_missing_fields_raises_error(self, store):
        """
        GIVEN meal data missing required fields
        WHEN log_meal() is called
        THEN ValueError is raised with field names
        """
        incomplete_meal = {"foods": ["apple"]}  # Missing calories, macros

        with pytest.raises(ValueError) as exc_info:
            store.log_meal("user_123", incomplete_meal)

        assert "calories" in str(exc_info.value)

    # Edge Case 2: New user no data
    def test_get_recent_new_user_returns_empty(self, store):
        """
        GIVEN user with no logged data
        WHEN get_recent() is called
        THEN empty list is returned
        """
        result = store.get_recent("brand_new_user")

        assert result == []

    # Edge Case 3: Boundary date inclusion
    def test_get_recent_includes_boundary_date(self, store, valid_meal):
        """
        GIVEN meal logged exactly 7 days ago
        WHEN get_recent(days=7) is called
        THEN that meal is included
        """
        user_id = "user_123"

        # Log meal with date 7 days ago
        store.log_meal(user_id, valid_meal, date=date.today() - timedelta(days=7))

        result = store.get_recent(user_id, days=7)

        assert len(result) == 1

    # Edge Case 4: Negative values
    def test_log_meal_negative_calories_raises_error(self, store):
        """
        GIVEN meal with negative calories
        WHEN log_meal() is called
        THEN ValueError is raised
        """
        bad_meal = {
            "time": "12:00",
            "foods": ["salad"],
            "calories": -100,  # Invalid
            "protein": 10,
            "carbs": 15,
            "fat": 5
        }

        with pytest.raises(ValueError) as exc_info:
            store.log_meal("user_123", bad_meal)

        assert "negative" in str(exc_info.value).lower()

    # Edge Case 5: Cleanup with nothing to clean
    def test_cleanup_no_expired_returns_zero(self, store):
        """
        GIVEN no expired records exist
        WHEN cleanup_expired() is called
        THEN 0 is returned
        """
        result = store.cleanup_expired()

        assert result == 0
```

```python
# memory/retriever.py - Edge Cases (5)
```

| # | Edge Case | Expected Behavior |
|---|-----------|-------------------|
| 1 | Query matches no intent patterns | Use default memory spec (all tiers, minimal) |
| 2 | User has no profile yet | Return empty long-term, prompt onboarding |
| 3 | Context exceeds total token budget | Prioritize: long-term > working > short-term, truncate |
| 4 | Query contains multiple intents | Merge memory specs, dedupe fields |
| 5 | Memory store connection fails | Return cached/empty context, log error |

**Unit Tests:**

```python
# tests/unit/test_memory/test_retriever.py

import pytest
from src.memory.retriever import MemoryRetriever


class TestMemoryRetriever:
    """Unit tests for MemoryRetriever class."""

    @pytest.fixture
    def retriever(self, mock_working, mock_short_term, mock_long_term):
        """Create MemoryRetriever with mocked stores."""
        return MemoryRetriever(
            working=mock_working,
            short_term=mock_short_term,
            long_term=mock_long_term,
            token_budgets={"working": 500, "short_term": 800, "long_term": 400}
        )

    # Edge Case 1: No intent match
    def test_retrieve_unknown_intent_uses_default(self, retriever):
        """
        GIVEN query matching no intent patterns
        WHEN retrieve_for_query() is called
        THEN default memory spec is used
        """
        result = retriever.retrieve_for_query("user_123", "xyz random gibberish")

        # Should return something from all tiers
        assert "long_term" in result
        assert "short_term" in result
        assert "working" in result

    # Edge Case 2: No profile exists
    def test_retrieve_no_profile_returns_empty_long_term(
        self, retriever, mock_long_term
    ):
        """
        GIVEN user with no profile
        WHEN retrieve_for_query() is called
        THEN long_term is empty string
        """
        mock_long_term.get.return_value = None

        result = retriever.retrieve_for_query("new_user", "how much protein?")

        assert result["long_term"] == ""

    # Edge Case 3: Token budget exceeded
    def test_retrieve_truncates_to_budget(self, retriever, mock_long_term):
        """
        GIVEN memory content exceeding token budget
        WHEN retrieve_for_query() is called
        THEN content is truncated to fit budget
        """
        # Mock returns very long content
        mock_long_term.get.return_value = Mock(
            injuries=["injury"] * 100,
            intolerances=["item"] * 100
        )

        result = retriever.retrieve_for_query("user_123", "workout plan")

        # 400 tokens * 4 chars ≈ 1600 chars max
        assert len(result["long_term"]) <= 1600

    # Edge Case 4: Multi-intent query
    def test_retrieve_multi_intent_merges_specs(self, retriever):
        """
        GIVEN query spanning multiple intents
        WHEN retrieve_for_query() is called
        THEN memory specs are merged
        """
        # Query mentions both food and exercise
        result = retriever.retrieve_for_query(
            "user_123",
            "what should I eat before my workout?"
        )

        # Should include both nutrition and fitness context
        assert result["long_term"]  # Has profile data
        assert result["short_term"]  # Has recent activity

    # Edge Case 5: Store connection fails
    def test_retrieve_handles_store_failure(self, retriever, mock_long_term):
        """
        GIVEN memory store raises exception
        WHEN retrieve_for_query() is called
        THEN empty context returned, error logged
        """
        mock_long_term.get.side_effect = ConnectionError("DB unavailable")

        result = retriever.retrieve_for_query("user_123", "any query")

        assert result["long_term"] == ""
        # Error should be logged (verify with caplog fixture)
```

---

### 3.4 Agents Module

**Files**: `base.py`, `trainer.py`, `nutritionist.py`, `recovery.py`, `router.py`
**Purpose**: Specialized agents with tool access

```python
# agents/router.py

class AgentRouter:
    """Route queries to appropriate agent(s)."""

    def route(self, query: str, context: Dict) -> List[str]:
        """
        Determine which agent(s) should handle the query.

        Args:
            query: User query
            context: Memory context

        Returns:
            List of agent names to invoke
        """
        pass
```

**Edge Cases (5):**

| # | Edge Case | Expected Behavior |
|---|-----------|-------------------|
| 1 | Query clearly maps to single agent | Return single agent |
| 2 | Query spans multiple domains | Return multiple agents |
| 3 | Query is ambiguous/general | Return all agents for collaborative response |
| 4 | Query is off-topic (not health-related) | Return empty list, polite decline |
| 5 | Query contains harmful intent | Return empty list, safety response |

**Unit Tests:**

```python
# tests/unit/test_agents/test_router.py

import pytest
from src.agents.router import AgentRouter


class TestAgentRouter:
    """Unit tests for AgentRouter class."""

    @pytest.fixture
    def router(self):
        """Create AgentRouter instance."""
        return AgentRouter()

    # Edge Case 1: Single domain
    def test_route_fitness_query_to_trainer(self, router):
        """
        GIVEN clear fitness query
        WHEN route() is called
        THEN only trainer agent returned
        """
        result = router.route("how many sets for biceps?", {})

        assert result == ["trainer"]

    # Edge Case 2: Multi-domain
    def test_route_complex_query_to_multiple(self, router):
        """
        GIVEN query spanning nutrition and fitness
        WHEN route() is called
        THEN both relevant agents returned
        """
        result = router.route(
            "what should I eat after leg day?",
            {}
        )

        assert "trainer" in result
        assert "nutritionist" in result

    # Edge Case 3: Ambiguous query
    def test_route_general_query_to_all(self, router):
        """
        GIVEN general/ambiguous health query
        WHEN route() is called
        THEN all agents returned
        """
        result = router.route("how can I feel better?", {})

        assert len(result) == 3  # All agents

    # Edge Case 4: Off-topic query
    def test_route_offtopic_returns_empty(self, router):
        """
        GIVEN non-health-related query
        WHEN route() is called
        THEN empty list returned
        """
        result = router.route("what's the capital of France?", {})

        assert result == []

    # Edge Case 5: Harmful query
    def test_route_harmful_query_returns_empty(self, router):
        """
        GIVEN query with harmful intent
        WHEN route() is called
        THEN empty list returned
        """
        result = router.route(
            "how to lose 20 pounds in one week?",  # Dangerous
            {}
        )

        assert result == []
```

---

### 3.5 Input Module

**Files**: `text.py`, `voice.py`, `image.py`
**Purpose**: Process multimodal inputs

```python
# input/image.py

class ImageProcessor:
    """Validate and analyze food images."""

    def validate(self, image_bytes: bytes) -> bool:
        """
        Validate image meets requirements.

        Args:
            image_bytes: Raw image data

        Returns:
            True if valid

        Raises:
            ValueError: If image fails validation
        """
        pass

    def analyze_food(self, image_bytes: bytes) -> FoodAnalysis:
        """
        Analyze food in image using Claude Vision.

        Args:
            image_bytes: Raw image data

        Returns:
            FoodAnalysis with detected foods and estimates
        """
        pass
```

**Edge Cases (5):**

| # | Edge Case | Expected Behavior |
|---|-----------|-------------------|
| 1 | Image over size limit (10MB) | Raise ValueError with size info |
| 2 | Unsupported format (GIF, BMP) | Raise ValueError listing supported formats |
| 3 | No food detected in image | Return FoodAnalysis with empty foods, message |
| 4 | Multiple foods in single image | Return all detected foods |
| 5 | Blurry/low-quality image | Return low_confidence flag, suggest retry |

**Unit Tests:**

```python
# tests/unit/test_input/test_image.py

import pytest
from src.input.image import ImageProcessor


class TestImageProcessor:
    """Unit tests for ImageProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create ImageProcessor instance."""
        return ImageProcessor(max_size_mb=10.0)

    @pytest.fixture
    def valid_food_image(self):
        """Load valid food image bytes."""
        # Small valid PNG
        return b'\x89PNG\r\n\x1a\n...'  # Actual test fixture

    # Edge Case 1: Oversized image
    def test_validate_oversized_raises_error(self, processor):
        """
        GIVEN image exceeding 10MB
        WHEN validate() is called
        THEN ValueError raised with size info
        """
        large_image = b"0" * (11 * 1024 * 1024)  # 11MB

        with pytest.raises(ValueError) as exc_info:
            processor.validate(large_image)

        assert "10mb" in str(exc_info.value).lower()

    # Edge Case 2: Unsupported format
    def test_validate_gif_raises_error(self, processor):
        """
        GIVEN GIF image
        WHEN validate() is called
        THEN ValueError raised listing supported formats
        """
        gif_header = b'GIF89a'

        with pytest.raises(ValueError) as exc_info:
            processor.validate(gif_header + b'\x00' * 100)

        assert "jpg" in str(exc_info.value).lower()
        assert "png" in str(exc_info.value).lower()

    # Edge Case 3: No food detected
    def test_analyze_landscape_returns_empty(self, processor, mock_vision):
        """
        GIVEN image with no food
        WHEN analyze_food() is called
        THEN FoodAnalysis has empty foods list
        """
        mock_vision.analyze.return_value = {"foods": []}
        landscape_image = b'...'  # Non-food image

        result = processor.analyze_food(landscape_image)

        assert result.detected_foods == []
        assert "no food" in result.message.lower()

    # Edge Case 4: Multiple foods
    def test_analyze_plate_returns_multiple(self, processor, mock_vision):
        """
        GIVEN image with multiple foods
        WHEN analyze_food() is called
        THEN all foods returned
        """
        mock_vision.analyze.return_value = {
            "foods": ["chicken", "rice", "broccoli"]
        }

        result = processor.analyze_food(b'plate_image_bytes')

        assert len(result.detected_foods) == 3
        assert "chicken" in result.detected_foods

    # Edge Case 5: Blurry image
    def test_analyze_blurry_returns_low_confidence(self, processor, mock_vision):
        """
        GIVEN blurry/low-quality image
        WHEN analyze_food() is called
        THEN low_confidence flag set
        """
        mock_vision.analyze.return_value = {
            "foods": ["possibly chicken"],
            "confidence": 0.3
        }

        result = processor.analyze_food(b'blurry_image')

        assert result.low_confidence is True
```

```python
# input/voice.py

class VoiceProcessor:
    """Process voice input via Whisper API."""

    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio to text.

        Args:
            audio_bytes: Raw audio data

        Returns:
            Transcribed text
        """
        pass
```

**Edge Cases (5):**

| # | Edge Case | Expected Behavior |
|---|-----------|-------------------|
| 1 | Audio longer than 30 seconds | Truncate to 30s, warn user |
| 2 | Audio with no speech | Return empty string with message |
| 3 | Unsupported audio format | Convert via ffmpeg or raise error |
| 4 | Whisper API timeout | Retry once, then return error |
| 5 | Heavy background noise | Return transcription with low_confidence |

**Unit Tests:**

```python
# tests/unit/test_input/test_voice.py

import pytest
from src.input.voice import VoiceProcessor


class TestVoiceProcessor:
    """Unit tests for VoiceProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create VoiceProcessor instance."""
        return VoiceProcessor(max_duration_sec=30)

    # Edge Case 1: Long audio
    def test_transcribe_long_audio_truncates(self, processor, mock_whisper):
        """
        GIVEN audio > 30 seconds
        WHEN transcribe() is called
        THEN audio truncated, transcription returned
        """
        long_audio = b"audio_data" * 10000  # Simulates long clip

        result = processor.transcribe(long_audio)

        # Verify truncation happened (mock would receive shorter audio)
        assert isinstance(result, str)

    # Edge Case 2: Silent audio
    def test_transcribe_silent_returns_empty(self, processor, mock_whisper):
        """
        GIVEN audio with no speech
        WHEN transcribe() is called
        THEN empty string returned
        """
        mock_whisper.transcribe.return_value = {"text": ""}

        result = processor.transcribe(b"silent_audio")

        assert result == ""

    # Edge Case 3: Unsupported format
    def test_transcribe_unsupported_format_converts(self, processor, mock_whisper):
        """
        GIVEN audio in unsupported format
        WHEN transcribe() is called
        THEN format converted before transcription
        """
        # WAV header
        wav_audio = b'RIFF' + b'\x00' * 100

        result = processor.transcribe(wav_audio)

        # Should succeed after conversion
        assert isinstance(result, str)

    # Edge Case 4: API timeout
    def test_transcribe_retries_on_timeout(self, processor, mock_whisper):
        """
        GIVEN Whisper API times out
        WHEN transcribe() is called
        THEN retry once before failing
        """
        mock_whisper.transcribe.side_effect = [
            TimeoutError("timeout"),
            {"text": "hello"}
        ]

        result = processor.transcribe(b"audio")

        assert result == "hello"
        assert mock_whisper.transcribe.call_count == 2

    # Edge Case 5: Noisy audio
    def test_transcribe_noisy_returns_low_confidence(self, processor, mock_whisper):
        """
        GIVEN audio with heavy background noise
        WHEN transcribe() is called
        THEN transcription returned with confidence info
        """
        mock_whisper.transcribe.return_value = {
            "text": "maybe hello",
            "confidence": 0.4
        }

        result, confidence = processor.transcribe_with_confidence(b"noisy")

        assert confidence < 0.5
```

---

### 3.6 Tools Module

**Files**: `food_db.py`, `exercise_db.py`, `calculators.py`
**Purpose**: External API wrappers and calculations

```python
# tools/food_db.py

def search_usda(food_name: str) -> Optional[NutritionInfo]:
    """
    Search USDA FoodData Central for nutrition info.

    Args:
        food_name: Food to search for

    Returns:
        NutritionInfo or None if not found
    """
    pass
```

**Edge Cases (5):**

| # | Edge Case | Expected Behavior |
|---|-----------|-------------------|
| 1 | Food not found in database | Return None |
| 2 | USDA API rate limit hit | Retry with backoff, cache aggressively |
| 3 | Ambiguous food name (multiple matches) | Return best match by relevance score |
| 4 | API returns malformed response | Log error, return None |
| 5 | Network timeout | Retry once, then return cached or None |

**Unit Tests:**

```python
# tests/unit/test_tools/test_food_db.py

import pytest
from src.tools.food_db import search_usda


class TestFoodDatabase:
    """Unit tests for food database functions."""

    # Edge Case 1: Not found
    def test_search_unknown_food_returns_none(self, mock_usda_api):
        """
        GIVEN food not in USDA database
        WHEN search_usda() is called
        THEN None returned
        """
        mock_usda_api.search.return_value = {"foods": []}

        result = search_usda("alien_fruit_xyz")

        assert result is None

    # Edge Case 2: Rate limit
    def test_search_rate_limit_retries(self, mock_usda_api):
        """
        GIVEN USDA API returns rate limit error
        WHEN search_usda() is called
        THEN retry with backoff
        """
        mock_usda_api.search.side_effect = [
            RateLimitError(),
            {"foods": [{"description": "apple", "nutrients": []}]}
        ]

        result = search_usda("apple")

        assert result is not None
        assert mock_usda_api.search.call_count == 2

    # Edge Case 3: Ambiguous query
    def test_search_ambiguous_returns_best_match(self, mock_usda_api):
        """
        GIVEN ambiguous food name with multiple matches
        WHEN search_usda() is called
        THEN best match by score returned
        """
        mock_usda_api.search.return_value = {
            "foods": [
                {"description": "Chicken breast, raw", "score": 0.9},
                {"description": "Chicken thigh, raw", "score": 0.7}
            ]
        }

        result = search_usda("chicken")

        assert "breast" in result.food_name.lower()

    # Edge Case 4: Malformed response
    def test_search_malformed_response_returns_none(self, mock_usda_api):
        """
        GIVEN API returns malformed data
        WHEN search_usda() is called
        THEN None returned, error logged
        """
        mock_usda_api.search.return_value = {"unexpected": "format"}

        result = search_usda("apple")

        assert result is None

    # Edge Case 5: Timeout
    def test_search_timeout_retries_then_none(self, mock_usda_api):
        """
        GIVEN network timeout
        WHEN search_usda() is called
        THEN retry once, then return None
        """
        mock_usda_api.search.side_effect = TimeoutError()

        result = search_usda("apple")

        assert result is None
        assert mock_usda_api.search.call_count == 2  # Original + 1 retry
```

---

## 4. Context Assembly Flow (Critical)

This is how memory flows into the LLM prompt:

```python
# core/context.py

class ContextAssembler:
    """
    Assemble final context for LLM from all sources.
    Respects token budgets and priority ordering.
    """

    def assemble(
        self,
        user_id: str,
        query: str,
        agent: str
    ) -> str:
        """
        Assemble complete context for LLM call.

        Priority order (if budget exceeded):
        1. System prompt (never truncated)
        2. User profile from long-term memory
        3. Current query
        4. Working memory (recent conversation)
        5. Retrieved RAG documents
        6. Short-term memory (recent activity)

        Args:
            user_id: User identifier
            query: Current user query
            agent: Agent handling this query

        Returns:
            Assembled prompt string within budget
        """
        pass
```

**Assembly Diagram:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTEXT ASSEMBLY                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [1] SYSTEM PROMPT (500 tokens) - FIXED                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ You are {agent_name}, a specialized coach for           │   │
│  │ adolescents. You have access to the user's profile      │   │
│  │ and recent activity...                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  [2] LONG-TERM MEMORY (400 tokens) - PRIORITY HIGH             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ User Profile:                                           │   │
│  │ - Age: 17, Weight: 70kg, Goal: build_muscle             │   │
│  │ - Injuries: left knee ACL (healing)                     │   │
│  │ - Intolerances: lactose                                 │   │
│  │ - Dietary preference: omnivore                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  [3] USER QUERY (200 tokens) - PRIORITY HIGH                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ User asks: "What should I eat before my leg workout?"   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  [4] WORKING MEMORY (500 tokens) - PRIORITY MEDIUM             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Recent conversation:                                    │   │
│  │ User: "I want to focus on legs this week"               │   │
│  │ Assistant: "Great! Given your knee, we'll modify..."    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  [5] RAG DOCUMENTS (1500 tokens) - PRIORITY MEDIUM             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Retrieved context:                                      │   │
│  │ [Doc 1] Pre-workout nutrition for strength training...  │   │
│  │ [Doc 2] Carbohydrate timing for muscle performance...   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  [6] SHORT-TERM MEMORY (800 tokens) - PRIORITY LOW             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Recent activity (last 7 days):                          │   │
│  │ - Yesterday: Upper body workout, 2100 cal consumed      │   │
│  │ - Sleep: avg 7.2 hrs, quality 3.5/5                     │   │
│  │ - Protein intake: avg 120g/day (below 140g target)      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ═══════════════════════════════════════════════════════════   │
│  TOTAL: ~3900 tokens → Sent to Claude                          │
│  RESPONSE BUDGET: ~1100 tokens remaining                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Test Organization

```
tests/
├── conftest.py                    # Shared fixtures
├── unit/                          # Unit tests (run first)
│   ├── test_ingestion/
│   │   ├── test_loader.py         # 5 edge cases
│   │   └── test_chunker.py        # 5 edge cases
│   ├── test_retrieval/
│   │   ├── test_embedder.py       # 5 edge cases
│   │   └── test_search.py         # 5 edge cases
│   ├── test_memory/
│   │   ├── test_working.py        # 5 edge cases
│   │   ├── test_short_term.py     # 5 edge cases
│   │   ├── test_long_term.py      # 5 edge cases
│   │   └── test_retriever.py      # 5 edge cases
│   ├── test_agents/
│   │   ├── test_trainer.py        # 5 edge cases
│   │   ├── test_nutritionist.py   # 5 edge cases
│   │   ├── test_recovery.py       # 5 edge cases
│   │   └── test_router.py         # 5 edge cases
│   ├── test_input/
│   │   ├── test_text.py           # 5 edge cases
│   │   ├── test_voice.py          # 5 edge cases
│   │   └── test_image.py          # 5 edge cases
│   └── test_tools/
│       ├── test_food_db.py        # 5 edge cases
│       ├── test_exercise_db.py    # 5 edge cases
│       └── test_calculators.py    # 5 edge cases
│
├── integration/                   # Integration tests (run after unit)
│   └── (defined after unit tests pass)
│
└── e2e/                          # End-to-end tests (run last)
    └── (defined after integration tests pass)
```

**Total unit tests: 18 test files × 5 edge cases = 90 tests**

---

## 6. Summary

| Principle | Implementation |
|-----------|----------------|
| Minimal code | 22 files, <100 lines each, single responsibility |
| Super modular | Each module independent, interfaces defined |
| Docstrings | Every function has Args, Returns, Raises |
| Memory-first | Query-aware retrieval, token budgets, priority truncation |
| Test-driven | 90 unit tests covering 5 edge cases per module |

**Next step**: Approve this design, then we write unit tests first before any implementation.
