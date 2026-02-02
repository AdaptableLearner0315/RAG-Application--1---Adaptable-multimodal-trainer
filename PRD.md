# PRD: Adaptive Adolescent Coaching Platform (AACP)

**Version**: 0.1.0 (MVP)
**Target Users**: Adolescents 16-19 years
**Core Differentiator**: Multi-agent coherence + Persistent adaptive memory

---

## 1. Problem Statement

Existing fitness/nutrition apps operate in silos. Users get a food tracker OR workout app OR sleep tracker—none connect the dots. Adolescents need holistic guidance that adapts to their changing bodies, schedules, and goals.

---

## 2. Solution

A team of AI coaching agents (Trainer, Nutritionist, Recovery Coach) that:
- Share context about the user
- Provide coherent cross-domain advice
- Learn and adapt over time via persistent memory
- Require NO fine-tuning—pure RAG + tool calling

---

## 3. MVP Scope

### 3.1 IN Scope

| Feature | Details |
|---------|---------|
| 3 AI Agents | Trainer, Nutritionist, Recovery Coach |
| Memory System | Working (session) + Short-term (7-day) + Long-term (permanent) |
| Text Input | Primary chat interface |
| Voice Input | Mic → Whisper API → text (no voice output) |
| Image Input | Food photo analysis via Claude Vision |
| User Profile | Onboarding: age, weight, goals, injuries, intolerances |
| Weekly Plans | Auto-adapting nutrition + workout + sleep plans |
| RAG Knowledge | Public datasets, no proprietary data |
| UI | Streamlit web app |

### 3.2 OUT of Scope (v1.1+)

- Mindset/Stress Coach agent
- Voice output (TTS)
- Real-time camera capture
- Meal planning calendar UI
- Social/community features
- Wearable integrations
- Push notifications

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              STREAMLIT UI                                   │
│                    [Chat] [Voice Mic] [Image Upload]                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INPUT PROCESSOR                                   │
│              ┌─────────┐  ┌─────────────┐  ┌──────────────┐                │
│              │  Text   │  │   Whisper   │  │    Claude    │                │
│              │ Parser  │  │  STT API    │  │   Vision     │                │
│              └────┬────┘  └──────┬──────┘  └──────┬───────┘                │
│                   └──────────────┴────────────────┘                        │
│                                  │                                          │
│                          Unified Text Query                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         QUERY ROUTER (LangGraph)                            │
│                                                                             │
│    Analyzes query → Routes to appropriate agent(s) → Orchestrates response │
│                                                                             │
│    Tools Available:                                                         │
│    • retrieve_nutrition_docs    • retrieve_exercise_docs                   │
│    • retrieve_sleep_docs        • get_user_profile                         │
│    • get_recent_activity        • update_user_memory                       │
│    • search_food_database       • analyze_food_image                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
          ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
          │   TRAINER   │  │ NUTRITIONIST│  │  RECOVERY   │
          │    AGENT    │  │    AGENT    │  │    COACH    │
          ├─────────────┤  ├─────────────┤  ├─────────────┤
          │ Tools:      │  │ Tools:      │  │ Tools:      │
          │ • exercise  │  │ • food_db   │  │ • sleep_db  │
          │   library   │  │ • nutrition │  │ • recovery  │
          │ • form_guide│  │   calculator│  │   protocols │
          │ • injury_mod│  │ • image_anal│  │ • rest_recs │
          └─────────────┘  └─────────────┘  └─────────────┘
                    │               │               │
                    └───────────────┴───────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MEMORY LAYER                                      │
│                                                                             │
│  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐        │
│  │  WORKING MEMORY   │ │  SHORT-TERM MEM   │ │  LONG-TERM MEM    │        │
│  │  (Redis/Session)  │ │  (SQLite 7-day)   │ │  (SQLite permanent)│        │
│  ├───────────────────┤ ├───────────────────┤ ├───────────────────┤        │
│  │ • Current convo   │ │ • Recent meals    │ │ • User profile    │        │
│  │ • Active context  │ │ • Recent workouts │ │ • Injuries list   │        │
│  │ • Retrieved docs  │ │ • Sleep logs      │ │ • Intolerances    │        │
│  │ • Pending tools   │ │ • Plan adherence  │ │ • Goals & prefs   │        │
│  │                   │ │ • Weekly patterns │ │ • Progress history│        │
│  └───────────────────┘ └───────────────────┘ └───────────────────┘        │
│                                    │                                        │
│                         ┌──────────▼──────────┐                            │
│                         │  PLAN ADAPTATION    │                            │
│                         │  ENGINE             │                            │
│                         │  (Weekly cron job)  │                            │
│                         └─────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RAG KNOWLEDGE BASES                               │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   NUTRITION     │  │    FITNESS      │  │  SLEEP/RECOVERY │            │
│  │   ChromaDB      │  │    ChromaDB     │  │    ChromaDB     │            │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤            │
│  │ • USDA FoodData │  │ • ExRx.net data │  │ • CDC guidelines│            │
│  │ • Dietary guide │  │ • Form guides   │  │ • Sleep hygiene │            │
│  │ • Adolescent    │  │ • Injury mods   │  │ • Recovery proto│            │
│  │   nutrition     │  │ • Teen programs │  │ • Rest day guide│            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Tech Stack

| Layer | Technology | Cost | Purpose |
|-------|------------|------|---------|
| **LLM** | Claude Sonnet 4.5 | API usage | Reasoning, tool calling, vision |
| **Speech-to-Text** | OpenAI Whisper API | Free tier / cheap | Voice → text |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | Free (local) | Document embeddings |
| **Vector Store** | ChromaDB | Free (local) | RAG retrieval |
| **Orchestration** | LangGraph | Free | Multi-agent routing |
| **Memory Store** | SQLite | Free | Short/long-term memory |
| **Session State** | Streamlit session_state | Free | Working memory |
| **Cache** | DiskCache | Free | Embedding/response cache |
| **UI** | Streamlit | Free | Web interface |
| **Food Database** | USDA FoodData Central API | Free | Nutrition lookup |
| **Exercise Data** | Scraped public sources (ExRx.net) | Free | Exercise library |
| **Image Analysis** | Claude Vision | API usage | Food photo analysis |

### 5.1 Free Public Data Sources

| Source | Data | URL |
|--------|------|-----|
| USDA FoodData Central | 300k+ foods with nutrients | https://fdc.nal.usda.gov/api-guide.html |
| Open Food Facts | Crowdsourced food DB | https://world.openfoodfacts.org/data |
| ExRx.net | Exercise library | https://exrx.net/Lists/Directory |
| CDC | Sleep guidelines | https://www.cdc.gov/sleep/ |
| WHO | Adolescent health guidelines | https://www.who.int/health-topics/adolescent-health |
| NIH | Dietary reference intakes | https://ods.od.nih.gov/HealthInformation/nutrientrecommendations.aspx |

---

## 6. Agent Specifications

### 6.1 Trainer Agent

**Role**: Fitness programming, exercise guidance, injury modifications

**Tools**:
| Tool | Input | Output |
|------|-------|--------|
| `retrieve_exercise_docs` | query: str | List[Document] |
| `get_exercise_by_muscle` | muscle_group: str | List[Exercise] |
| `get_injury_modifications` | exercise: str, injury: str | ModifiedExercise |
| `get_user_fitness_history` | user_id: str | FitnessLog |

**System Prompt Context**:
```
You are a certified fitness trainer specializing in adolescent athletes.
You have access to the user's injury history and fitness level.
Always provide injury-safe alternatives when relevant.
Never recommend exercises contraindicated for the user's conditions.
```

### 6.2 Nutritionist Agent

**Role**: Meal guidance, macro tracking, food analysis

**Tools**:
| Tool | Input | Output |
|------|-------|--------|
| `retrieve_nutrition_docs` | query: str | List[Document] |
| `search_food_database` | food_name: str | NutritionInfo |
| `analyze_food_image` | image_base64: str | FoodAnalysis |
| `calculate_daily_needs` | user_profile: Profile | MacroTargets |
| `get_user_diet_history` | user_id: str | DietLog |

**System Prompt Context**:
```
You are a registered dietitian specializing in adolescent nutrition.
You have access to the user's intolerances, allergies, and dietary preferences.
Always flag foods that conflict with user restrictions.
Tailor advice for growing adolescent bodies (higher protein, calcium needs).
```

### 6.3 Recovery Coach Agent

**Role**: Sleep optimization, rest days, recovery protocols

**Tools**:
| Tool | Input | Output |
|------|-------|--------|
| `retrieve_sleep_docs` | query: str | List[Document] |
| `get_user_sleep_history` | user_id: str | SleepLog |
| `get_recovery_protocol` | activity_type: str, intensity: str | RecoveryPlan |
| `assess_recovery_needs` | user_id: str | RecoveryAssessment |

**System Prompt Context**:
```
You are a recovery specialist for adolescent athletes.
Adolescents need 8-10 hours of sleep for optimal development.
Consider recent workout intensity when recommending rest.
Connect sleep quality to next-day performance recommendations.
```

---

## 7. Memory System Design

### 7.1 Memory Schema

```python
# Long-term Memory (permanent)
class UserProfile:
    user_id: str
    created_at: datetime

    # Demographics
    age: int
    height_cm: float
    weight_kg: float
    gender: str

    # Health Context
    injuries: List[Injury]           # {type, severity, date, status}
    intolerances: List[str]          # ["lactose", "gluten"]
    allergies: List[str]             # ["peanuts"]
    dietary_preference: str          # "omnivore" | "vegetarian" | "vegan"

    # Goals
    primary_goal: str                # "build_muscle" | "lose_fat" | "improve_energy"
    target_weight_kg: Optional[float]
    activity_level: str              # "sedentary" | "moderate" | "active" | "athlete"

    # Learned Preferences (auto-updated)
    preferred_exercises: List[str]
    disliked_foods: List[str]
    typical_wake_time: time
    typical_sleep_time: time

# Short-term Memory (7-day rolling window)
class RecentActivity:
    user_id: str
    date: date

    meals: List[MealLog]             # {time, foods, calories, macros}
    workouts: List[WorkoutLog]       # {time, exercises, duration, intensity}
    sleep: SleepLog                  # {bed_time, wake_time, quality_1_10}

    plan_adherence: float            # 0.0 - 1.0
    notes: str                       # User-reported context

# Working Memory (session only)
class SessionContext:
    conversation_history: List[Message]
    retrieved_documents: List[Document]
    active_agent: str
    pending_tool_calls: List[ToolCall]
```

### 7.2 Memory Update Rules

| Trigger | Action |
|---------|--------|
| User mentions new injury | Add to `injuries` in long-term memory |
| User reports food reaction | Add to `intolerances` in long-term memory |
| User logs meal | Add to `meals` in short-term memory |
| User completes workout | Add to `workouts` in short-term memory |
| 7 days pass | Archive short-term → Extract patterns → Update long-term preferences |
| User explicitly corrects | Immediate long-term memory update |

### 7.3 Plan Adaptation Logic

```
Weekly Adaptation Job (every Sunday):

1. ANALYZE short-term memory
   - Workout completion rate
   - Meal plan adherence
   - Sleep consistency
   - Reported energy/mood

2. DETECT patterns
   - Skipped morning workouts → Shift to evening
   - Consistently under protein → Increase protein-rich meal suggestions
   - Poor sleep before leg days → Adjust schedule

3. ADJUST next week's plan
   - Modify workout schedule
   - Update meal suggestions
   - Adjust sleep recommendations

4. PROMOTE learnings to long-term memory
   - Update preferred_exercises
   - Update typical_wake_time
   - Update activity patterns
```

---

## 8. Edge Cases & Handling

### 8.1 Ingestion Module

| Edge Case | Handling | Test |
|-----------|----------|------|
| PDF with no extractable text (scanned) | Return error, suggest re-upload | `test_scanned_pdf_rejected` |
| PDF > 50MB | Reject with size error | `test_oversized_pdf_rejected` |
| Corrupted PDF | Catch PyPDF error, return user-friendly message | `test_corrupted_pdf_handled` |
| PDF with mixed languages | Process anyway, flag low-confidence chunks | `test_multilingual_pdf` |
| Empty PDF | Return error, no chunks created | `test_empty_pdf_rejected` |
| PDF with only images | Extract nothing, warn user | `test_image_only_pdf` |

### 8.2 Retrieval Module

| Edge Case | Handling | Test |
|-----------|----------|------|
| Query returns 0 results | Fall back to web search | `test_zero_results_fallback` |
| All results below similarity threshold | Return best match with confidence warning | `test_low_confidence_results` |
| ChromaDB connection failure | Retry 3x, then return cached results or error | `test_db_connection_retry` |
| Query too long (>512 tokens) | Truncate with warning | `test_query_truncation` |
| Ambiguous query (matches multiple domains) | Return results from all relevant collections | `test_multi_domain_query` |
| Offensive/harmful query | Refuse, log incident | `test_harmful_query_blocked` |

### 8.3 Memory Module

| Edge Case | Handling | Test |
|-----------|----------|------|
| User profile not found | Trigger onboarding flow | `test_missing_profile_onboarding` |
| Conflicting memory updates | Latest timestamp wins | `test_conflicting_updates` |
| Memory storage full | Archive oldest short-term, warn user | `test_memory_storage_limit` |
| User requests data deletion | Purge all memory, confirm | `test_gdpr_deletion` |
| Corrupted memory file | Restore from backup, log error | `test_corrupted_memory_recovery` |
| Impossible values (negative weight) | Reject update, ask for correction | `test_invalid_profile_data` |

### 8.4 Image Module

| Edge Case | Handling | Test |
|-----------|----------|------|
| Non-food image uploaded | Return "no food detected" message | `test_non_food_image` |
| Blurry/dark image | Request better image | `test_low_quality_image` |
| Image > 10MB | Compress or reject | `test_oversized_image` |
| Unsupported format (GIF, BMP) | Convert or reject with format list | `test_unsupported_format` |
| Multiple foods in image | List all detected items | `test_multi_food_image` |
| Nutrition label image | Extract text, parse nutrition facts | `test_nutrition_label` |
| Image with personal info visible | Process food only, ignore PII | `test_pii_in_image` |

### 8.5 Voice Module

| Edge Case | Handling | Test |
|-----------|----------|------|
| Audio > 30 seconds | Truncate with warning | `test_long_audio_truncated` |
| No speech detected | Return "couldn't hear you" message | `test_silent_audio` |
| Heavy background noise | Return low-confidence transcript, ask to retry | `test_noisy_audio` |
| Non-English speech | Attempt transcription, warn if confidence low | `test_non_english_audio` |
| Whisper API timeout | Retry once, then fall back to text input | `test_whisper_timeout` |
| Unsupported audio format | Convert via ffmpeg or reject | `test_unsupported_audio` |

### 8.6 Agent Routing

| Edge Case | Handling | Test |
|-----------|----------|------|
| Query spans multiple domains | Invoke multiple agents, merge responses | `test_multi_agent_query` |
| No agent matches query | Default to general response, ask clarifying question | `test_unroutable_query` |
| Agent tool call fails | Retry with fallback tool, or apologize | `test_tool_failure_recovery` |
| Circular agent calls | Max depth limit (3), break cycle | `test_circular_agent_prevention` |
| Conflicting agent advice | Trainer + Nutritionist disagree → Present both with reasoning | `test_conflicting_advice` |

### 8.7 Generation Module

| Edge Case | Handling | Test |
|-----------|----------|------|
| Context exceeds token limit | Truncate oldest conversation turns | `test_context_overflow` |
| LLM returns refusal | Log, return safe default response | `test_llm_refusal` |
| LLM hallucinates food data | Cross-check with USDA API before presenting | `test_hallucination_check` |
| LLM returns malformed JSON (tool call) | Retry with stricter prompt | `test_malformed_tool_response` |
| Rate limit hit | Exponential backoff, queue request | `test_rate_limit_handling` |
| API key invalid/expired | Immediate error, notify admin | `test_invalid_api_key` |

### 8.8 Profile Module

| Edge Case | Handling | Test |
|-----------|----------|------|
| User under 16 | Reject registration, show age requirement | `test_underage_rejection` |
| Extreme values (height 300cm) | Flag for review, don't save | `test_extreme_values` |
| Missing required fields | Block progress until complete | `test_incomplete_profile` |
| User changes injury status | Update all dependent recommendations | `test_injury_status_change` |
| Contradictory preferences (vegan + loves steak) | Ask for clarification | `test_contradictory_preferences` |

---

## 9. Test Specifications

### 9.1 Unit Tests

```python
# tests/unit/test_ingestion.py

class TestPDFLoader:
    def test_valid_pdf_extraction(self, sample_pdf):
        """Extract text from valid PDF."""

    def test_scanned_pdf_rejected(self, scanned_pdf):
        """Reject PDFs with no extractable text."""

    def test_oversized_pdf_rejected(self, large_pdf):
        """Reject PDFs exceeding 50MB limit."""

    def test_corrupted_pdf_handled(self, corrupted_pdf):
        """Handle corrupted PDF gracefully."""

    def test_empty_pdf_rejected(self, empty_pdf):
        """Reject PDFs with no content."""


class TestChunker:
    def test_chunk_size_within_limits(self, sample_text):
        """All chunks between min and max size."""

    def test_chunk_overlap_preserved(self, sample_text):
        """Chunks have specified overlap."""

    def test_semantic_boundaries_respected(self, sample_text):
        """Chunks break at semantic boundaries."""

    def test_empty_text_returns_empty_list(self):
        """Empty input returns empty chunk list."""

    def test_single_sentence_not_split(self, short_text):
        """Text shorter than min_chunk stays intact."""


# tests/unit/test_retrieval.py

class TestVectorSearch:
    def test_returns_top_k_results(self, populated_db, query):
        """Returns exactly k results."""

    def test_results_sorted_by_similarity(self, populated_db, query):
        """Results ordered by descending similarity."""

    def test_similarity_threshold_filtering(self, populated_db, query):
        """Filters results below threshold."""

    def test_empty_collection_returns_empty(self, empty_db, query):
        """Empty DB returns empty list."""

    def test_query_embedding_cached(self, populated_db, query, cache):
        """Same query uses cached embedding."""


class TestWebSearch:
    def test_returns_expected_count(self, mock_ddg):
        """Returns configured number of results."""

    def test_timeout_handling(self, slow_mock_ddg):
        """Handles timeout gracefully."""

    def test_empty_results_handled(self, empty_mock_ddg):
        """Handles no results gracefully."""

    def test_results_cached(self, mock_ddg, cache):
        """Results cached for TTL period."""


# tests/unit/test_memory.py

class TestWorkingMemory:
    def test_add_message(self, session):
        """Add message to conversation history."""

    def test_context_retrieval(self, session_with_history):
        """Retrieve full context."""

    def test_clear_session(self, session_with_history):
        """Clear all session data."""


class TestShortTermMemory:
    def test_log_meal(self, user_id, meal_data):
        """Log meal to short-term memory."""

    def test_log_workout(self, user_id, workout_data):
        """Log workout to short-term memory."""

    def test_7_day_window(self, user_id, old_data):
        """Data older than 7 days not returned."""

    def test_get_recent_activity(self, user_id):
        """Retrieve recent activity summary."""


class TestLongTermMemory:
    def test_create_profile(self, profile_data):
        """Create new user profile."""

    def test_update_profile(self, user_id, update_data):
        """Update existing profile."""

    def test_add_injury(self, user_id, injury_data):
        """Add injury to profile."""

    def test_get_profile(self, user_id):
        """Retrieve complete profile."""

    def test_delete_profile(self, user_id):
        """Delete profile and all data."""


# tests/unit/test_image.py

class TestImageValidator:
    def test_valid_image_accepted(self, valid_jpg):
        """Accept valid JPG image."""

    def test_oversized_image_rejected(self, large_image):
        """Reject images over size limit."""

    def test_unsupported_format_rejected(self, gif_image):
        """Reject unsupported formats."""

    def test_dimensions_validated(self, huge_dimension_image):
        """Reject images exceeding max dimensions."""


class TestFoodAnalyzer:
    def test_food_detected(self, food_image, mock_vision):
        """Detect food in image."""

    def test_non_food_rejected(self, landscape_image, mock_vision):
        """Return appropriate message for non-food."""

    def test_multiple_foods_listed(self, plate_image, mock_vision):
        """List all foods in multi-food image."""

    def test_nutrition_label_parsed(self, label_image, mock_vision):
        """Extract nutrition facts from label."""


# tests/unit/test_voice.py

class TestAudioProcessor:
    def test_valid_audio_transcribed(self, valid_audio, mock_whisper):
        """Transcribe valid audio clip."""

    def test_long_audio_truncated(self, long_audio, mock_whisper):
        """Truncate audio over 30 seconds."""

    def test_silent_audio_handled(self, silent_audio, mock_whisper):
        """Handle audio with no speech."""

    def test_format_conversion(self, wav_audio, mock_whisper):
        """Convert unsupported formats."""


# tests/unit/test_agents.py

class TestTrainerAgent:
    def test_exercise_recommendation(self, user_profile, query):
        """Recommend appropriate exercises."""

    def test_injury_modification(self, user_with_injury, exercise):
        """Provide injury-safe modifications."""

    def test_uses_fitness_history(self, user_with_history, query):
        """Consider past workouts in advice."""


class TestNutritionistAgent:
    def test_meal_suggestion(self, user_profile, query):
        """Suggest appropriate meals."""

    def test_intolerance_filtering(self, user_with_intolerance, foods):
        """Filter out intolerant foods."""

    def test_macro_calculation(self, user_profile):
        """Calculate correct macro targets."""


class TestRecoveryCoach:
    def test_sleep_recommendation(self, user_profile, query):
        """Recommend appropriate sleep duration."""

    def test_rest_day_suggestion(self, user_with_heavy_week):
        """Suggest rest when needed."""

    def test_recovery_protocol(self, recent_workout):
        """Provide workout-specific recovery advice."""


# tests/unit/test_router.py

class TestQueryRouter:
    def test_fitness_query_to_trainer(self, fitness_query):
        """Route fitness queries to trainer."""

    def test_food_query_to_nutritionist(self, food_query):
        """Route food queries to nutritionist."""

    def test_sleep_query_to_recovery(self, sleep_query):
        """Route sleep queries to recovery coach."""

    def test_multi_domain_query_routing(self, complex_query):
        """Route to multiple agents when needed."""

    def test_ambiguous_query_handling(self, vague_query):
        """Handle ambiguous queries appropriately."""
```

### 9.2 Integration Tests

```python
# tests/integration/test_ingestion_pipeline.py

class TestIngestionPipeline:
    def test_pdf_to_vectorstore(self, sample_pdf, chroma_db):
        """PDF → chunks → embeddings → stored in ChromaDB."""

    def test_duplicate_pdf_handling(self, sample_pdf, chroma_db):
        """Skip already-ingested documents."""

    def test_batch_ingestion(self, pdf_directory, chroma_db):
        """Ingest multiple PDFs in batch."""


# tests/integration/test_retrieval_pipeline.py

class TestRetrievalPipeline:
    def test_query_to_results(self, populated_db, query):
        """Query → embedding → search → ranked results."""

    def test_hybrid_search(self, populated_db, web_mock, query):
        """Combine vector + web search results."""

    def test_cache_integration(self, populated_db, cache, query):
        """Verify caching at each layer."""

    def test_fallback_on_empty_results(self, empty_db, web_mock, query):
        """Fall back to web when vector search empty."""


# tests/integration/test_memory_pipeline.py

class TestMemoryPipeline:
    def test_onboarding_to_profile(self, onboarding_data):
        """Onboarding flow creates complete profile."""

    def test_conversation_to_memory(self, conversation, user_id):
        """Conversation extracts and stores relevant info."""

    def test_weekly_adaptation(self, user_with_week_data):
        """Weekly job analyzes and adapts plan."""

    def test_memory_retrieval_in_context(self, user_id, query):
        """Memory correctly injected into agent context."""


# tests/integration/test_agent_pipeline.py

class TestAgentPipeline:
    def test_single_agent_flow(self, user_profile, fitness_query):
        """Query → router → agent → tool calls → response."""

    def test_multi_agent_collaboration(self, user_profile, complex_query):
        """Multiple agents contribute to single response."""

    def test_tool_call_execution(self, agent, tool_query):
        """Agent correctly invokes and uses tool results."""

    def test_memory_update_after_response(self, agent, query, memory):
        """Relevant info extracted and stored after interaction."""


# tests/integration/test_image_pipeline.py

class TestImagePipeline:
    def test_upload_to_analysis(self, food_image, mock_vision):
        """Image upload → validation → analysis → response."""

    def test_analysis_to_logging(self, food_image, mock_vision, memory):
        """Analyzed food logged to short-term memory."""

    def test_nutrition_lookup_integration(self, food_image, mock_vision, food_db):
        """Detected food → USDA lookup → enriched response."""


# tests/integration/test_voice_pipeline.py

class TestVoicePipeline:
    def test_audio_to_response(self, audio_clip, mock_whisper, agent):
        """Audio → transcription → agent → response."""

    def test_transcription_error_recovery(self, noisy_audio, mock_whisper):
        """Handle transcription errors gracefully."""


# tests/integration/test_end_to_end.py

class TestEndToEnd:
    def test_new_user_journey(self, streamlit_app):
        """
        Complete new user flow:
        1. Onboarding
        2. First question
        3. Image upload
        4. Follow-up question (tests memory)
        """

    def test_returning_user_journey(self, streamlit_app, existing_user):
        """
        Returning user flow:
        1. Login
        2. System recalls profile
        3. Question references past data
        4. Plan adaptation visible
        """

    def test_cross_domain_coherence(self, streamlit_app, user_with_history):
        """
        Ask question spanning domains:
        "I have leg day tomorrow but slept poorly, what should I eat?"
        Verify response integrates all three agents.
        """
```

---

## 10. API Contracts

### 10.1 Internal Tool Schemas

```python
# Retrieval Tools
@tool
def retrieve_nutrition_docs(query: str, top_k: int = 5) -> List[Document]:
    """Retrieve relevant nutrition documents from vector store."""

@tool
def retrieve_exercise_docs(query: str, top_k: int = 5) -> List[Document]:
    """Retrieve relevant exercise documents from vector store."""

@tool
def retrieve_sleep_docs(query: str, top_k: int = 5) -> List[Document]:
    """Retrieve relevant sleep/recovery documents from vector store."""

# Food Database Tools
@tool
def search_food_database(food_name: str) -> NutritionInfo:
    """Search USDA database for food nutrition info."""

@tool
def analyze_food_image(image_base64: str) -> FoodAnalysis:
    """Analyze food image using Claude Vision."""

# Memory Tools
@tool
def get_user_profile(user_id: str) -> UserProfile:
    """Retrieve user's long-term profile."""

@tool
def get_recent_activity(user_id: str, days: int = 7) -> RecentActivity:
    """Retrieve user's recent activity from short-term memory."""

@tool
def update_user_memory(user_id: str, update: MemoryUpdate) -> bool:
    """Update user's memory with new information."""

# Fitness Tools
@tool
def get_exercise_by_muscle(muscle_group: str) -> List[Exercise]:
    """Get exercises targeting specific muscle group."""

@tool
def get_injury_modifications(exercise: str, injury: str) -> ModifiedExercise:
    """Get injury-safe modification for exercise."""

# Calculation Tools
@tool
def calculate_daily_needs(profile: UserProfile) -> MacroTargets:
    """Calculate daily macro/calorie needs based on profile."""

@tool
def assess_recovery_needs(user_id: str) -> RecoveryAssessment:
    """Assess recovery needs based on recent activity."""
```

### 10.2 Response Schemas

```python
class NutritionInfo(BaseModel):
    food_name: str
    serving_size: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    micronutrients: Dict[str, float]

class FoodAnalysis(BaseModel):
    detected_foods: List[str]
    confidence: float
    estimated_calories: float
    estimated_macros: Dict[str, float]
    warnings: List[str]  # e.g., "Contains nuts"

class Exercise(BaseModel):
    name: str
    muscle_groups: List[str]
    equipment: List[str]
    difficulty: str
    instructions: List[str]
    contraindications: List[str]

class ModifiedExercise(BaseModel):
    original: Exercise
    modification: str
    reason: str
    alternative: Optional[Exercise]

class MacroTargets(BaseModel):
    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int
    fiber_g: int
    water_ml: int

class RecoveryAssessment(BaseModel):
    fatigue_level: str  # "low" | "moderate" | "high"
    recommended_rest: bool
    recovery_activities: List[str]
    sleep_recommendation_hours: float
```

---

## 11. Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Onboarding completion | >80% | Users who complete full profile |
| Return rate (day 3) | >40% | Users who return within 3 days |
| Cross-domain query satisfaction | >70% | User rates response as helpful |
| Memory recall accuracy | >90% | System correctly recalls user info |
| Image analysis accuracy | >80% | Correct food identification |
| Voice transcription accuracy | >90% | Correct transcription |
| Response latency (p95) | <5s | Time to first response token |

---

## 12. Timeline (Development Phases)

| Phase | Focus | Deliverable |
|-------|-------|-------------|
| 1 | Core Infrastructure | Config, memory schemas, basic Streamlit shell |
| 2 | RAG Pipeline | Ingestion, chunking, vector store, retrieval |
| 3 | Single Agent | Nutritionist agent with tools, working memory |
| 4 | Multi-Agent | Add Trainer + Recovery, router, cross-domain |
| 5 | Multimodal Input | Image analysis, voice transcription |
| 6 | Adaptation Engine | Weekly plan adaptation, long-term learning |
| 7 | Polish | Error handling, edge cases, testing |

---

## 13. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Claude API costs spike | High | Implement aggressive caching, token budgets |
| Whisper API rate limits | Medium | Queue requests, show "processing" state |
| Food image misidentification | Medium | Always show confidence, allow user correction |
| Memory bloat | Medium | Enforce TTLs, archive old data |
| Harmful health advice | High | Add safety guardrails, refuse extreme recommendations |
| User data privacy | High | Local storage only (MVP), clear deletion path |

---

## 14. Open Questions

1. Should we support offline mode (cached responses)?
2. Do we need parental consent flow for 16-17 year olds?
3. Should agents cite sources in responses?
4. How do we handle users with eating disorders (detection + referral)?
5. Multi-language support needed for MVP?
