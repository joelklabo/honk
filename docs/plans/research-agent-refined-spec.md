# Research Agent - Refined Production Specification

**Version:** 2.0.0  
**Created:** 2025-11-18  
**Status:** Ready for Implementation  
**Purpose:** Self-improving research specialist with persistent memory and exponential learning capability

---

## Executive Summary

This specification defines a **self-improving research agent** that learns from every research session and gets exponentially better over time. Unlike traditional static agents, this agent:

- ✅ **Remembers** past research sessions and what strategies worked
- ✅ **Learns** from successes and failures
- ✅ **Improves** continuously with each research session
- ✅ **Adapts** strategies based on topic types and context
- ✅ **Self-reflects** on its own research process

**Key Innovation:** Persistent memory system enabling exponential improvement rather than static performance.

---

## Architecture Overview

### Three-Layer System

```
┌─────────────────────────────────────────────────┐
│  Research Agent Instructions (Agent Layer)      │
│  - Research modes                               │
│  - Search strategies                            │
│  - Synthesis patterns                           │
│  - Quality validation                           │
└─────────────────────────────────────────────────┘
                    ↓ uses ↑ updates
┌─────────────────────────────────────────────────┐
│  Memory System (Infrastructure Layer)           │
│  - SessionRecorder: Records each research       │
│  - StrategyManager: Tracks what works           │
│  - KnowledgeBase: Reusable insights             │
└─────────────────────────────────────────────────┘
                    ↓ stores ↑ retrieves
┌─────────────────────────────────────────────────┐
│  Persistent Storage (Data Layer)                │
│  - sessions.json: Past research history         │
│  - strategies.json: Successful patterns         │
│  - knowledge-base.json: Topic insights          │
└─────────────────────────────────────────────────┘
```

### File Locations

**Memory Storage:**
```
~/.copilot/research-memory/
├── sessions.json              # All past research sessions
├── strategies.json            # Validated patterns (what works/doesn't)
└── knowledge-base.json        # Topic-specific insights
```

**Agent Definition:**
```
~/.copilot/agents/research.agent.md         # User's personal copy
.github/agents/research.agent.md            # Project-specific copy
<org>/.github/agents/research.agent.md      # Organization-wide copy
```

---

## Component 1: Research Agent Instructions

### Core Structure

**YAML Frontmatter:**
```yaml
---
name: research
description: Self-improving research specialist with exponential learning capability
version: 2.0.0
tools:
  - web_search (required)
  - bash (for memory system)
  - create/edit/view (for note-taking)
capabilities:
  - Multi-hop web research
  - Source synthesis and deduplication
  - Persistent memory and strategy learning
  - Self-improvement and meta-reflection
memory_enabled: true
memory_location: ~/.copilot/research-memory/
---
```

**Instructions (Markdown):**
Seven phases covering the complete research workflow with memory integration.

### Phase Breakdown

#### Phase 0: Memory Check (NEW - Critical Innovation)
**Before starting research, check what was learned before:**

1. **Scan sessions.json** for similar past research topics
2. **Review strategies.json** for patterns that worked
3. **Check knowledge-base.json** for topic-specific insights
4. **Tell user what was found** and how it will be applied
5. **Adjust research plan** based on past learnings

**Why Critical:**
Without this phase, all learning is wasted. The agent must actively USE memory to benefit from past experience.

**Example Output:**
```
"I see I've researched similar topics before:
- GraphQL basics (Session 42, Deep Dive mode, quality score 8/10)
- iOS networking patterns (Session 38, Implementation Guide)

From past experience, I learned:
- Official docs + Apollo guides are best sources
- Filter by 2024-2025 for latest iOS patterns
- Cross-reference with URLSession patterns

I'll apply these successful strategies. Shall I proceed?"
```

#### Phase 1: Clarification (Incorporating Past Context)
**Ask user for research parameters while incorporating memory:**

1. **Research Mode Selection** (suggest mode that worked before if applicable):
   - Quick Reference (30 min, 3-5 searches)
   - Deep Dive (1-2 hours, 10-15 searches)
   - Comparison Analysis (30-45 min, 5-8 searches)
   - Current State Check (15-20 min, 3-4 searches)
   - Implementation Guide (1 hour, 7-10 searches)
   - Problem Solution (30-45 min, 4-7 searches)

2. **Context Questions**:
   - Specific context? (e.g., "Building iOS app")
   - Intended use? (e.g., "Create an agent", "Write docs")
   - Constraints? (e.g., "iOS 17+ only")
   - Knowledge level? (Beginner / Intermediate / Expert)

3. **Scope Confirmation**:
   ```
   I'll research [TOPIC] using [MODE] approach.
   
   Planned searches:
   1. [Search query 1]
   2. [Search query 2]
   ...
   
   Expected deliverable: [Description]
   Time estimate: [X minutes]
   
   Should I proceed?
   ```

#### Phase 2: Research Execution
**Multi-angle search strategy with pattern application:**

**Search Angles:**
- Fundamentals (core concepts, official docs)
- Best Practices (expert recommendations)
- Real-World Usage (code examples, tutorials)
- Common Pitfalls (known issues, debugging)
- Current State (2024-2025 updates)
- Comparison (alternative approaches)
- Expert Opinions (blogs, talks)

**Query Patterns (from strategies.json):**
```
# If strategy database shows "version + year" works for this topic type:
"[Technology] [Feature] 2024 2025"
"[Technology] best practices [Version] 2025"

# If past sessions show official docs are best starting point:
"[Technology] official documentation"
→ Then deeper searches based on findings
```

**Iterative Refinement:**
- After initial searches → Assess depth
- Found contradictions? → Search for clarification
- Missing perspectives? → Search alternative sources
- New angles discovered? → Pivot to explore them

**Source Quality Evaluation:**
1. ✅ Official docs (framework maintainers, Apple, etc.)
2. ✅ Expert blogs (known developers, companies)
3. ✅ Recent content (2024-2025 preferred)
4. ✅ GitHub (code examples, issues)
5. ⚠️ Stack Overflow (validate date and votes)
6. ❌ Outdated content (pre-2023 for fast-moving tech)

#### Phase 3: Synthesis & Organization
**Deduplicate and organize findings:**

**Deduplication Rules:**
- 3+ sources say same thing → Mention once with all citations
- Sources contradict → Explain why (old vs new, different contexts)
- Extract common patterns → These are standards/best practices

**Organization Hierarchy:**
```
1. Executive Summary (3-5 bullets)
2. Core Concepts (general → specific)
3. Practical Patterns (with code examples)
4. Best Practices (recommendations)
5. Common Pitfalls (mistakes to avoid)
6. Comparison/Tradeoffs (if applicable)
7. Current State (2024-2025 specifics)
8. References (organized by type)
```

**Use Tables for Comparisons:**
```markdown
| Aspect | Option A | Option B |
|--------|----------|----------|
| Performance | Fast | Moderate |
| Learning Curve | Steep | Gentle |
| Best For | Large apps | Simple apps |
```

#### Phase 4: Deliverable Formatting
**Mode-specific templates:**

- **Quick Reference:** TL;DR, core concepts, quick start, watch-outs
- **Deep Dive:** Comprehensive guide with full examples and patterns
- **Comparison:** Side-by-side table with decision framework
- **Implementation:** Step-by-step with complete working code
- **Current State:** What's new, what's deprecated, migration notes
- **Problem Solution:** Root cause analysis with solutions

*(Full templates defined in appendix)*

#### Phase 5: Quality Validation
**Before delivering, self-check:**

**Completeness:**
- ✅ Answered original question?
- ✅ Covered all requested aspects?
- ✅ Provided code examples where needed?
- ✅ Included 2024-2025 information?
- ✅ Addressed common pitfalls?

**Quality:**
- ✅ Deduplicated repeated info?
- ✅ Organized logically?
- ✅ Used tables for comparisons?
- ✅ Cited sources clearly?
- ✅ Resolved contradictions?

**Actionability:**
- ✅ Clear recommendations?
- ✅ Practical examples?
- ✅ Decision frameworks?
- ✅ "What next" guidance?

#### Phase 6: Session Recording (CRITICAL)
**After completing research, ALWAYS record:**

**Session Record Structure:**
```json
{
  "id": "session-[timestamp]",
  "timestamp": "[ISO 8601 datetime]",
  "topic": "[Research topic]",
  "mode": "[Mode used]",
  "searches_conducted": [number],
  "time_taken_minutes": [estimated],
  "quality_score": [1-10],
  "sources_used": [count],
  "what_worked": [
    "[Successful strategy 1]",
    "[Successful strategy 2]"
  ],
  "what_didnt_work": [
    "[Failed approach 1]",
    "[Failed approach 2]"
  ],
  "learnings": [
    "[Key insight 1]",
    "[Key insight 2]"
  ]
}
```

**Quality Score Scale:**
- 1-3: Poor (missing key information)
- 4-6: Adequate (covers basics)
- 7-8: Good (comprehensive, actionable)
- 9-10: Excellent (exceptional depth, novel insights)

**What to Record:**
- Which search queries found best sources?
- Which approach yielded most insights?
- What made synthesis effective?
- What took too much time for little value?
- What patterns emerged?
- What would you do differently?

**Write to Memory:**
```bash
# Append to ~/.copilot/research-memory/sessions.json
# Memory system handles JSON formatting and validation
```

#### Phase 7: Meta-Reflection (Self-Improvement Analysis)
**Analyze your own research process:**

**Questions to Answer:**

1. **Did Past Learnings Help?**
   - Which strategies from memory were applied?
   - How much time did they save?
   - Did quality improve?

2. **What's New?**
   - New patterns worth generalizing?
   - Novel approach that worked better?
   - Insights about research process itself?

3. **How Am I Improving?**
   - Compare to baseline (Session 1)
   - Time: Faster or slower?
   - Quality: Higher scores?
   - Efficiency: More insights per search?
   - Calculate improvement metrics

4. **What Should I Focus On Next?**
   - Which research mode needs practice?
   - Which topic types are still challenging?
   - Which skills are weakest?

5. **Update Strategies Database**
   - If pattern validated → Increase confidence
   - If new insight → Add to knowledge base
   - If pattern failed → Document why

**Example Meta-Reflection:**
```
Session 45: GraphQL iOS best practices
Time: 60 min (baseline was 90 min) → 33% improvement ✅
Quality: 9/10 (baseline was 7/10) → +2 points ✅
Efficiency: 0.9 insights/search (baseline 0.5) → 80% improvement ✅

Applied: "Version + Year" pattern from Session 42 (saved 20 min)
New insight: Organizing by use case > organizing by library
Next focus: Improve Comparison mode efficiency (still 50 min, target 35)

Trend: Exponential improvement trajectory maintained ✅
```

**Improvement Trajectory Tracking:**
```
Session 1:  90 min, 7/10 quality, 0.5 efficiency
Session 10: 75 min, 7.5/10 quality, 0.6 efficiency
Session 20: 65 min, 8/10 quality, 0.7 efficiency
Session 30: 62 min, 8.5/10 quality, 0.8 efficiency
Session 45: 60 min, 9/10 quality, 0.9 efficiency

Projection (Session 100): 45 min, 9.5/10 quality, 1.0 efficiency
```

---

## Component 2: Memory System Infrastructure

### Overview

The memory system is the foundation that enables self-improvement. It consists of three core managers and three JSON storage files.

### Class: SessionRecorder

**Purpose:** Record and retrieve research sessions

**Location:** `src/honk/internal/memory/session_recorder.py`

**Methods:**

```python
class SessionRecorder:
    """Records research sessions for learning and improvement."""
    
    def __init__(self, storage_path: Path = Path.home() / ".copilot" / "research-memory"):
        self.storage_path = storage_path
        self.sessions_file = storage_path / "sessions.json"
        self._ensure_storage()
    
    def record_session(self, session: ResearchSession) -> None:
        """Record a completed research session."""
        # Validate session schema
        # Append to sessions.json
        # Update statistics
    
    def get_sessions(
        self,
        topic_pattern: Optional[str] = None,
        mode: Optional[str] = None,
        min_quality: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[ResearchSession]:
        """Retrieve past sessions matching criteria."""
        # Load sessions.json
        # Filter by criteria
        # Return sorted by relevance/recency
    
    def find_similar_topics(self, topic: str) -> List[ResearchSession]:
        """Find past sessions on similar topics."""
        # Use keyword matching + semantic similarity
        # Return ranked by relevance
    
    def get_statistics(self) -> SessionStatistics:
        """Get aggregate statistics across all sessions."""
        # Total sessions, average quality, time trends
        # Improvement trajectory
```

**Data Model:**

```python
@dataclass
class ResearchSession:
    """Single research session record."""
    id: str                          # session-[timestamp]
    timestamp: datetime
    topic: str
    mode: str                        # Which research mode
    searches_conducted: int
    time_taken_minutes: int
    quality_score: int               # 1-10
    sources_used: int
    what_worked: List[str]           # Successful strategies
    what_didnt_work: List[str]       # Failed approaches
    learnings: List[str]             # Key insights
    metadata: Dict[str, Any]         # Extensible
```

**Storage Format (sessions.json):**

```json
{
  "version": "1.0.0",
  "sessions": [
    {
      "id": "session-20251118-120000",
      "timestamp": "2025-11-18T12:00:00Z",
      "topic": "Swift 6 concurrency patterns",
      "mode": "Deep Dive",
      "searches_conducted": 12,
      "time_taken_minutes": 90,
      "quality_score": 8,
      "sources_used": 15,
      "what_worked": [
        "Starting with Apple's official Swift 6 migration guide",
        "Including version + year in queries"
      ],
      "what_didnt_work": [
        "Generic 'Swift concurrency' returned too much Swift 5 content"
      ],
      "learnings": [
        "For language version topics, ALWAYS include version + year",
        "Apple docs are best starting point for Swift"
      ]
    }
  ]
}
```

### Class: StrategyManager

**Purpose:** Track which strategies work and which don't

**Location:** `src/honk/internal/memory/strategy_manager.py`

**Methods:**

```python
class StrategyManager:
    """Manages research strategies and patterns."""
    
    def __init__(self, storage_path: Path = Path.home() / ".copilot" / "research-memory"):
        self.storage_path = storage_path
        self.strategies_file = storage_path / "strategies.json"
        self._ensure_storage()
    
    def record_success(
        self,
        pattern_name: str,
        topic_type: str,
        description: str,
        example_query: Optional[str] = None,
        context: Optional[str] = None
    ) -> None:
        """Record a successful strategy pattern."""
        # Load strategies.json
        # Find or create pattern
        # Increment success count
        # Update confidence score
    
    def record_failure(
        self,
        pattern_name: str,
        topic_type: str,
        why_failed: str,
        better_alternative: Optional[str] = None
    ) -> None:
        """Record a failed strategy pattern."""
        # Load strategies.json
        # Find or create failure record
        # Increment failure count
        # Document root cause
    
    def get_strategies_for_topic(
        self,
        topic_type: str,
        min_confidence: float = 0.7
    ) -> List[Strategy]:
        """Get recommended strategies for a topic type."""
        # Load strategies.json
        # Filter by topic type
        # Sort by success rate
        # Return high-confidence strategies
    
    def get_patterns_to_avoid(self, topic_type: str) -> List[FailedPattern]:
        """Get patterns that have failed for this topic type."""
        # Load strategies.json
        # Filter failures by topic type
        # Return with explanations
    
    def update_confidence(self, pattern_name: str, success: bool) -> None:
        """Update confidence score based on new usage."""
        # Bayesian update or simple moving average
```

**Data Model:**

```python
@dataclass
class Strategy:
    """Successful research strategy pattern."""
    pattern_name: str
    topic_type: str                  # programming_language, framework, tool, etc.
    success_rate: float              # 0.0 to 1.0
    times_used: int
    confidence: str                  # low, medium, high
    description: str
    example_query: Optional[str]
    when_to_use: str
    last_validated: datetime

@dataclass
class FailedPattern:
    """Failed strategy pattern (anti-pattern)."""
    pattern_name: str
    topic_type: str
    failure_rate: float
    times_tried: int
    why_failed: str
    better_alternative: Optional[str]
```

**Storage Format (strategies.json):**

```json
{
  "version": "1.0.0",
  "successful_strategies": [
    {
      "pattern_name": "Version + Year Query Pattern",
      "topic_type": "programming_language",
      "success_rate": 0.95,
      "times_used": 15,
      "confidence": "high",
      "description": "Include version number and year in search queries",
      "example_query": "Swift 6 concurrency 2025",
      "when_to_use": "When researching language features, frameworks with versions",
      "last_validated": "2025-11-18T12:00:00Z"
    }
  ],
  "failed_patterns": [
    {
      "pattern_name": "Generic Query Without Version",
      "topic_type": "programming_language",
      "failure_rate": 0.85,
      "times_tried": 10,
      "why_failed": "Returns mixed results from multiple versions",
      "better_alternative": "Use 'Version + Year Query Pattern' instead"
    }
  ]
}
```

### Class: KnowledgeBase

**Purpose:** Store reusable topic-specific insights

**Location:** `src/honk/internal/memory/knowledge_base.py`

**Methods:**

```python
class KnowledgeBase:
    """Manages topic-specific knowledge and insights."""
    
    def __init__(self, storage_path: Path = Path.home() / ".copilot" / "research-memory"):
        self.storage_path = storage_path
        self.kb_file = storage_path / "knowledge-base.json"
        self._ensure_storage()
    
    def add_insight(
        self,
        topic_category: str,
        insight: str,
        source_sessions: List[str],
        confidence: str = "provisional"
    ) -> None:
        """Add a new insight to the knowledge base."""
        # Validate not duplicate
        # Add to appropriate topic category
        # Track source sessions for validation
    
    def get_insights_for_topic(self, topic_category: str) -> List[Insight]:
        """Get all insights for a topic category."""
        # Load knowledge-base.json
        # Filter by category
        # Return sorted by confidence
    
    def update_topic_guidance(
        self,
        topic_category: str,
        best_sources: List[str],
        avoid: List[str],
        search_template: str
    ) -> None:
        """Update guidance for a topic category."""
        # Update or create topic category
        # Merge with existing guidance
    
    def validate_insight(self, insight_id: str) -> None:
        """Promote insight from provisional to validated."""
        # Increment validation count
        # Upgrade confidence if threshold reached
```

**Data Model:**

```python
@dataclass
class Insight:
    """Reusable insight about a topic."""
    id: str
    topic_category: str
    insight: str
    discovered: datetime
    validated_count: int
    confidence: str                  # provisional, validated, high_confidence
    source_sessions: List[str]       # Session IDs that contributed

@dataclass
class TopicGuidance:
    """Guidance for researching a topic category."""
    category: str
    key_insight: str
    best_sources: List[str]
    avoid: List[str]
    search_template: str
    examples: List[str]
```

**Storage Format (knowledge-base.json):**

```json
{
  "version": "1.0.0",
  "topic_categories": {
    "programming_languages": {
      "key_insight": "Always specify version and year for language features",
      "best_sources": [
        "Official language documentation",
        "Language team blogs",
        "Expert developer blogs"
      ],
      "avoid": [
        "Generic tutorials without version",
        "Pre-2023 content for fast-changing languages"
      ],
      "search_template": "[Language] [Feature] [Version] 2025",
      "examples": [
        "Swift 6 concurrency 2025",
        "Python 3.12 pattern matching tutorial 2025"
      ]
    },
    "frameworks": {
      "key_insight": "Frameworks change rapidly, prioritize last 6 months",
      "best_sources": [
        "Official framework docs",
        "Maintainer blogs",
        "GitHub repos and issues"
      ],
      "avoid": [
        "Outdated tutorials",
        "Abandoned blog posts"
      ],
      "search_template": "[Framework] [Feature] [Version] best practices 2025"
    }
  },
  "insights": [
    {
      "id": "insight-001",
      "topic_category": "programming_languages",
      "insight": "For Swift topics, Apple's official documentation is the best starting point, then cross-reference with Paul Hudson and Swift team blogs",
      "discovered": "2025-11-17T10:00:00Z",
      "validated_count": 8,
      "confidence": "high_confidence",
      "source_sessions": [
        "session-20251117-100000",
        "session-20251118-110000"
      ]
    }
  ]
}
```

---

## Component 3: Memory Integration Workflow

### Initialization (First Use)

**When agent runs for the first time:**

```python
# Check if memory directory exists
if not (Path.home() / ".copilot" / "research-memory").exists():
    # Create directory structure
    # Initialize empty JSON files with schema version
    # Log initialization
    print("✅ Research memory system initialized at ~/.copilot/research-memory/")
```

### Research Workflow with Memory

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User requests research                                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Phase 0: Memory Check                                    │
│    - SessionRecorder.find_similar_topics(topic)             │
│    - StrategyManager.get_strategies_for_topic(type)         │
│    - KnowledgeBase.get_insights_for_topic(category)         │
│    → Tell user what was found and how it will be applied    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Phase 1: Clarification                                   │
│    - Ask mode, context, constraints                         │
│    - Incorporate past learnings into plan                   │
│    - Confirm scope with user                                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Phase 2-3: Research & Synthesis                          │
│    - Apply successful strategies from memory                │
│    - Avoid failed patterns                                  │
│    - Use topic-specific search templates                    │
│    - Track what works/doesn't work in this session          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Phase 4-5: Format & Validate                             │
│    - Deliver formatted result                               │
│    - Self-check quality                                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Phase 6: Session Recording (CRITICAL)                    │
│    - Self-assess quality score (1-10)                       │
│    - Identify what worked / what didn't                     │
│    - Extract learnings                                      │
│    - SessionRecorder.record_session(session)                │
│    → Session saved to sessions.json                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Phase 7: Meta-Reflection                                 │
│    - Compare to baseline and past sessions                  │
│    - Calculate improvement metrics                          │
│    - Identify new patterns                                  │
│    - StrategyManager.record_success/failure()               │
│    - KnowledgeBase.add_insight()                            │
│    → Strategies updated, insights recorded                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. Next Research Session Benefits                           │
│    → All past learnings available from start                │
│    → Faster, higher quality research                        │
│    → Exponential improvement over time                      │
└─────────────────────────────────────────────────────────────┘
```

### Memory Update Triggers

**When to record success:**
- Search query found excellent sources → Record query pattern
- Organization approach worked well → Record synthesis strategy
- Topic-specific approach succeeded → Record in knowledge base
- Quality score ≥ 8 → Validate contributing strategies

**When to record failure:**
- Search query wasted time → Record as anti-pattern
- Approach led to poor results → Document why it failed
- Sources were unreliable → Update topic guidance
- Quality score ≤ 5 → Analyze what went wrong

**When to update confidence:**
- Strategy used successfully → Increment success count, recalculate confidence
- Strategy used unsuccessfully → Increment failure count, lower confidence
- Pattern validated 3+ times → Promote to "high confidence"
- Pattern failed 3+ times → Mark as anti-pattern with better alternative

---

## Component 4: Agent Template Implementation

### File Structure

**research.agent.md:**

```markdown
---
name: research
description: Self-improving research specialist with exponential learning capability
version: 2.0.0
tools:
  - web_search
  - bash
  - create
  - edit
  - view
capabilities:
  - Multi-hop web research
  - Source synthesis and deduplication
  - Persistent memory and strategy learning
  - Self-improvement and meta-reflection
memory_enabled: true
memory_location: ~/.copilot/research-memory/
---

# Research Agent Instructions

You are an expert research specialist who conducts thorough web research and synthesizes findings into actionable, well-organized knowledge.

## Your Core Mission

Transform vague research requests into comprehensive, well-cited, actionable knowledge by:
1. **Clarifying** the research goal through interactive questions
2. **Researching** using multi-hop, iterative web searches
3. **Synthesizing** information with deduplication and organization
4. **Delivering** structured output in the appropriate format
5. **Learning** from every session to continuously improve

## Memory System

You have a persistent memory that enables you to learn and improve:

**Memory Location:** `~/.copilot/research-memory/`
- `sessions.json` - All past research sessions
- `strategies.json` - What strategies work and don't work
- `knowledge-base.json` - Topic-specific insights

**Critical Rule:** ALWAYS check memory before starting new research!

---

## Phase 0: Memory Check (ALWAYS START HERE)

**Before asking the user anything, check if you've researched this topic before.**

```bash
# Check for similar past research
# Review successful strategies
# Check for topic-specific insights
```

**If found similar research, tell the user:**
```
"I see I've researched similar topics before:
- [Topic 1] (Session X, [date], quality score Y/10)
- [Topic 2] (Session Z, [date])

Based on past experience, I know that:
- [Key learning 1]
- [Key learning 2]

I'll apply these learnings to this research."
```

**Implementation in agent:**
```bash
# Agent instruction pseudo-code
if memory_exists:
    similar_sessions = find_similar_topics(current_topic)
    relevant_strategies = get_strategies_for_topic(topic_type)
    insights = get_insights_for_topic(topic_category)
    
    if similar_sessions or relevant_strategies or insights:
        report_findings_to_user()
        adjust_research_plan_based_on_memory()
```

---

## Phase 1-5: Research Execution

[Include all research modes, search strategies, synthesis patterns from Phase 1-5 above]

---

## Phase 6: Session Recording (REQUIRED AFTER EVERY RESEARCH)

**After completing research, ALWAYS record the session.**

**Template for recording:**
```json
{
  "id": "session-[timestamp]",
  "timestamp": "[ISO 8601]",
  "topic": "[What was researched]",
  "mode": "[Which mode used]",
  "searches_conducted": [number],
  "time_taken_minutes": [estimate],
  "quality_score": [1-10 self-assessment],
  "sources_used": [count],
  "what_worked": [
    "[Strategy that succeeded]",
    "[Query pattern that found good sources]"
  ],
  "what_didnt_work": [
    "[Approach that failed]",
    "[Query that wasted time]"
  ],
  "learnings": [
    "[Insight 1]",
    "[Insight 2]"
  ]
}
```

**Quality Score Scale:**
- 1-3: Poor (missing key information, low source quality)
- 4-6: Adequate (covers basics, could be deeper)
- 7-8: Good (comprehensive, well-sourced, actionable)
- 9-10: Excellent (exceptional depth, novel insights)

**How to record:**
```bash
# Write session record to ~/.copilot/research-memory/sessions.json
# Memory system handles validation and appending
```

---

## Phase 7: Meta-Reflection (REQUIRED)

**After recording session, analyze your own performance.**

**Questions to answer:**

1. **Did Past Learnings Help?**
   - Which strategies from memory were applied?
   - How much time did they save?
   - Did quality improve?

2. **What's New?**
   - New patterns worth generalizing?
   - Novel approach that worked better?

3. **How Am I Improving?**
   - Compare to baseline (Session 1)
   - Time: Faster or slower?
   - Quality: Higher scores?
   - Efficiency: More insights per search?

4. **What Should I Focus On Next?**
   - Which mode needs practice?
   - Which topic types are challenging?
   - Which skills are weakest?

5. **Update Strategies Database**
   - Successful pattern? → Record success
   - Failed pattern? → Record failure
   - New insight? → Add to knowledge base

**Example reflection:**
```
Session 45: GraphQL iOS best practices
Time: 60 min (vs baseline 90 min) → 33% faster ✅
Quality: 9/10 (vs baseline 7/10) → +2 points ✅
Efficiency: 0.9 insights/search (vs 0.5) → 80% better ✅

Applied: Version + Year pattern (saved 20 min)
New: Organizing by use case > by library
Focus: Improve Comparison mode (still 50 min, target 35)

Trend: Exponential improvement maintained ✅
```

**Update memory:**
```bash
# Record successful strategies
# Record failed patterns
# Add new insights
# Update confidence scores
```

---

## Success Metrics

You've succeeded when:
- ✅ User can implement/decide/understand based on your research
- ✅ Information is current and accurate (2024-2025)
- ✅ Sources are credible and properly cited
- ✅ Output matches requested mode/depth
- ✅ Quality score ≥ 7
- ✅ Session recorded for future learning
- ✅ Memory updated with new insights

**Remember:** Every research session makes you smarter. Use that intelligence!

---

## Version History

### v2.0.0 - Self-Improvement System (2025-11-18)
- Added persistent memory system
- Added session recording
- Added strategy learning
- Added meta-reflection
- Result: Agent now learns and improves over time

---

**You are not just a research tool. You are a learning system that gets better with every session.**
```

---

## Component 5: Testing Strategy

### Memory System Tests

**Unit Tests (`tests/internal/test_memory_system.py`):**

```python
def test_session_recorder_initialization():
    """Test memory directory and files are created."""
    
def test_record_session():
    """Test session is properly recorded to JSON."""
    
def test_find_similar_topics():
    """Test similar topic detection."""
    
def test_session_statistics():
    """Test aggregate statistics calculation."""

def test_strategy_manager_record_success():
    """Test successful strategy recording."""
    
def test_strategy_manager_record_failure():
    """Test failed pattern recording."""
    
def test_get_strategies_for_topic():
    """Test strategy retrieval and filtering."""
    
def test_confidence_updates():
    """Test Bayesian confidence updates."""

def test_knowledge_base_add_insight():
    """Test insight creation and validation."""
    
def test_knowledge_base_topic_guidance():
    """Test topic guidance updates."""
    
def test_insight_validation():
    """Test insight promotion from provisional to validated."""
```

**Integration Tests (`tests/tools/agent/test_memory_integration.py`):**

```python
def test_memory_check_phase():
    """Test agent checks memory before starting research."""
    
def test_session_recording_phase():
    """Test agent records session after completing research."""
    
def test_strategy_application():
    """Test agent applies strategies from memory."""
    
def test_improvement_over_time():
    """Test quality improves across multiple sessions."""
```

**Contract Tests (`tests/contract/test_memory_schema.py`):**

```python
def test_session_json_schema():
    """Validate sessions.json against schema."""
    
def test_strategy_json_schema():
    """Validate strategies.json against schema."""
    
def test_knowledge_base_json_schema():
    """Validate knowledge-base.json against schema."""
```

### End-to-End Tests

**Scenario 1: First-Time Use**
```python
def test_first_time_research_session():
    """Test agent with no prior memory."""
    # Given: Empty memory system
    # When: Agent conducts first research
    # Then: Memory initialized, session recorded
```

**Scenario 2: Learning from Past Session**
```python
def test_apply_past_learnings():
    """Test agent uses insights from previous session."""
    # Given: One completed session in memory
    # When: Agent researches similar topic
    # Then: Applies strategies from first session, improves time/quality
```

**Scenario 3: Continuous Improvement**
```python
def test_exponential_improvement():
    """Test agent improves over multiple sessions."""
    # Given: 10 completed sessions
    # When: Conduct 11th session
    # Then: Time < average, quality > average
```

---

## Component 6: User Experience

### First-Time Setup

**When user first uses research agent:**

```
$ gh copilot --agent research

🎉 Welcome to the Research Agent!

This agent learns from every research session and gets better over time.

Setting up memory system...
✅ Created ~/.copilot/research-memory/
✅ Initialized sessions.json
✅ Initialized strategies.json
✅ Initialized knowledge-base.json

Memory system ready! This is your first research session (baseline).

What would you like me to research?
> 
```

### Subsequent Sessions

**When user returns:**

```
$ gh copilot --agent research

📚 Research Agent (Session 12)

Memory status:
- 11 past research sessions recorded
- 8 validated strategies learned
- 15 insights in knowledge base
- Average quality score: 8.2/10
- Improvement: 40% faster than baseline

What would you like me to research?
> Swift 6 concurrency patterns

🔍 Checking memory for past research...

Found similar topics:
- Swift concurrency basics (Session 5, quality 7/10, 6 months ago)
- Swift async/await patterns (Session 8, quality 8/10, 3 months ago)

Applying learned strategies:
✅ Version + Year query pattern (success rate 95%)
✅ Start with Apple official docs (worked in 8/11 Swift sessions)
✅ Cross-reference Swift team blogs

Ready to proceed with improved approach!
```

### After Research

**Session recording:**

```
✅ Research complete!

Session Summary:
- Time: 55 minutes (baseline: 90 min, improvement: 39% faster)
- Searches: 10
- Sources: 12
- Quality: 9/10 (self-assessed)

📝 Recording session...
✅ Session recorded to memory
✅ Strategies updated (2 successes, 0 failures)
✅ New insight added to Swift topic knowledge

🎯 Meta-Reflection:
Improvement trajectory: On track for exponential growth
Next session projection: 50 min, 9.5/10 quality

You're getting smarter! 🚀
```

---

## Component 7: Maintenance & Evolution

### Memory Cleanup

**Prevent memory bloat:**

```python
# After N sessions, cleanup
def cleanup_memory(max_sessions: int = 1000):
    """Keep memory lean and focused."""
    # Archive old sessions (> 1 year)
    # Remove low-confidence strategies (< 0.3 after 10+ uses)
    # Consolidate duplicate insights
```

### Backup & Export

**User can backup memory:**

```bash
# Backup command
$ honk agent memory backup
✅ Memory backed up to ~/.copilot/research-memory-backup-2025-11-18.tar.gz

# Export for sharing
$ honk agent memory export --anonymized
✅ Exported anonymized strategies to ~/research-strategies-export.json
# (Removes personal topics, keeps patterns)
```

### Memory Analytics

**User can view learning progress:**

```bash
$ honk agent memory stats

Research Memory Analytics
=========================

Total Sessions: 45
Time Period: 2025-01-15 to 2025-11-18 (10 months)

Improvement Metrics:
- Time efficiency: 40% faster than baseline
- Quality improvement: +2.1 points average
- Search efficiency: 0.9 insights/search (vs 0.5 baseline)

Top Strategies (by success rate):
1. Version + Year Query (95%, 15 uses)
2. Official Docs First (92%, 20 uses)
3. Organize by Concept (88%, 12 uses)

Topic Mastery:
- Programming Languages: Expert (18 sessions, avg quality 8.8)
- Frameworks: Proficient (12 sessions, avg quality 8.2)
- Tools: Developing (8 sessions, avg quality 7.5)

Trajectory: Exponential improvement ✅
Next Milestone: Session 50 (projected 45 min, 9.5/10 quality)
```

---

## Implementation Checklist

### Phase 1: Memory Infrastructure
- [ ] Create `src/honk/internal/memory/` module
- [ ] Implement `SessionRecorder` class
- [ ] Implement `StrategyManager` class
- [ ] Implement `KnowledgeBase` class
- [ ] Create JSON schemas for memory files
- [ ] Write unit tests for each class
- [ ] Test memory initialization
- [ ] Test concurrent access safety

### Phase 2: Agent Template
- [ ] Create `research.agent.md` template
- [ ] Include all 7 phases in instructions
- [ ] Add memory integration hooks
- [ ] Add usage examples
- [ ] Test template validation
- [ ] Document memory system usage

### Phase 3: Integration
- [ ] Hook memory check into agent startup (Phase 0)
- [ ] Hook session recording into agent completion (Phase 6)
- [ ] Hook meta-reflection into agent completion (Phase 7)
- [ ] Test full workflow end-to-end
- [ ] Verify memory updates correctly

### Phase 4: Testing
- [ ] Unit tests for memory system (15+ tests)
- [ ] Integration tests for agent workflow (5+ tests)
- [ ] Contract tests for JSON schemas (3+ tests)
- [ ] End-to-end tests for improvement (3+ scenarios)
- [ ] Performance tests (memory size, lookup speed)

### Phase 5: Documentation
- [ ] User guide for research agent
- [ ] Technical spec for memory system
- [ ] API documentation for memory classes
- [ ] Examples and tutorials
- [ ] Troubleshooting guide

### Phase 6: Polish
- [ ] Rich console output for memory status
- [ ] Progress indicators during research
- [ ] Error handling and recovery
- [ ] Memory backup/restore commands
- [ ] Analytics and reporting

---

## Success Criteria

**System is successful when:**

1. ✅ **Memory Persistence**: All research sessions are recorded and retrieved correctly
2. ✅ **Learning Application**: Agent uses past learnings in new sessions (measurable time savings)
3. ✅ **Continuous Improvement**: Quality scores trend upward over time
4. ✅ **Pattern Recognition**: Successful strategies are identified and reused
5. ✅ **Anti-Pattern Avoidance**: Failed approaches are documented and avoided
6. ✅ **User Visibility**: Users can see learning progress and memory stats
7. ✅ **Reliability**: Memory system handles errors gracefully, doesn't lose data
8. ✅ **Performance**: Memory lookups are fast (<100ms)
9. ✅ **Scalability**: System handles 1000+ sessions without degradation
10. ✅ **Exponential Growth**: Improvement curve is exponential, not linear

**Validation Metrics:**

```
Baseline (Session 1):
- Time: 90 minutes
- Quality: 7/10
- Efficiency: 0.5 insights/search

Target (Session 50):
- Time: 45 minutes (50% improvement)
- Quality: 9/10 (+2 points)
- Efficiency: 1.0 insights/search (100% improvement)

Target (Session 100):
- Time: 30-40 minutes (60% improvement)
- Quality: 9.5/10 (+2.5 points)
- Efficiency: 1.2 insights/search (140% improvement)
```

---

## Appendices

### Appendix A: Research Mode Templates

*(Full templates for Quick Reference, Deep Dive, Comparison Analysis, Current State Check, Implementation Guide, Problem Solution)*

### Appendix B: Search Query Patterns

*(Comprehensive list of proven query patterns by topic type)*

### Appendix C: Memory JSON Schemas

**sessions.json Schema:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "version": { "type": "string" },
    "sessions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "timestamp": { "type": "string", "format": "date-time" },
          "topic": { "type": "string" },
          "mode": { "type": "string" },
          "searches_conducted": { "type": "integer" },
          "time_taken_minutes": { "type": "integer" },
          "quality_score": { "type": "integer", "minimum": 1, "maximum": 10 },
          "sources_used": { "type": "integer" },
          "what_worked": { "type": "array", "items": { "type": "string" } },
          "what_didnt_work": { "type": "array", "items": { "type": "string" } },
          "learnings": { "type": "array", "items": { "type": "string" } }
        },
        "required": ["id", "timestamp", "topic", "mode", "quality_score"]
      }
    }
  }
}
```

**strategies.json Schema:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "version": { "type": "string" },
    "successful_strategies": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "pattern_name": { "type": "string" },
          "topic_type": { "type": "string" },
          "success_rate": { "type": "number", "minimum": 0, "maximum": 1 },
          "times_used": { "type": "integer" },
          "confidence": { "type": "string", "enum": ["low", "medium", "high"] },
          "description": { "type": "string" },
          "example_query": { "type": "string" },
          "when_to_use": { "type": "string" },
          "last_validated": { "type": "string", "format": "date-time" }
        },
        "required": ["pattern_name", "topic_type", "success_rate", "times_used"]
      }
    },
    "failed_patterns": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "pattern_name": { "type": "string" },
          "topic_type": { "type": "string" },
          "failure_rate": { "type": "number" },
          "times_tried": { "type": "integer" },
          "why_failed": { "type": "string" },
          "better_alternative": { "type": "string" }
        },
        "required": ["pattern_name", "topic_type", "why_failed"]
      }
    }
  }
}
```

**knowledge-base.json Schema:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "version": { "type": "string" },
    "topic_categories": {
      "type": "object",
      "patternProperties": {
        ".*": {
          "type": "object",
          "properties": {
            "key_insight": { "type": "string" },
            "best_sources": { "type": "array", "items": { "type": "string" } },
            "avoid": { "type": "array", "items": { "type": "string" } },
            "search_template": { "type": "string" },
            "examples": { "type": "array", "items": { "type": "string" } }
          }
        }
      }
    },
    "insights": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "topic_category": { "type": "string" },
          "insight": { "type": "string" },
          "discovered": { "type": "string", "format": "date-time" },
          "validated_count": { "type": "integer" },
          "confidence": { "type": "string" },
          "source_sessions": { "type": "array", "items": { "type": "string" } }
        },
        "required": ["id", "topic_category", "insight"]
      }
    }
  }
}
```

### Appendix D: Example Session Evolution

**Session 1 (Baseline):**
- Topic: Swift concurrency
- Mode: Deep Dive
- Time: 90 minutes
- Searches: 15
- Quality: 7/10
- What worked: Used official Apple docs
- What didn't work: Generic queries returned Swift 5 content
- Learning: Need version-specific queries

**Session 5:**
- Topic: SwiftUI animations
- Mode: Deep Dive
- Time: 75 minutes (17% faster)
- Quality: 7.5/10
- Applied: Version-specific queries (from Session 1)
- What worked: Including "iOS 17" in queries
- Learning: Pattern generalizes beyond Swift language to Apple tech

**Session 15:**
- Topic: GraphQL iOS integration
- Mode: Deep Dive
- Time: 62 minutes (31% faster)
- Quality: 8.5/10
- Applied: Version + year pattern, official docs first
- What worked: Organizing by use case instead of library
- Learning: Use case organization > library organization for API topics

**Session 30:**
- Topic: Core Data migration patterns
- Mode: Implementation Guide
- Time: 55 minutes (39% faster)
- Quality: 9/10
- Applied: All previous learnings + use case organization
- What worked: Everything - agent is now expert level
- Learning: Continuous improvement validated

**Session 50 (Projected):**
- Time: 45 minutes (50% faster than baseline)
- Quality: 9.5/10
- Efficiency: Near-optimal
- Status: **Expert-level mastery achieved** ✅

---

## Conclusion

This specification defines a **self-improving research agent** that:

1. **Has persistent memory** of all past research sessions
2. **Learns from experience** by tracking what works and what doesn't
3. **Applies past learnings** to new research sessions automatically
4. **Improves exponentially** over time, not linearly
5. **Self-reflects** on its own process and adjusts strategies
6. **Provides transparency** to users about its learning progress

**The key innovation is Phase 0 (Memory Check)** - making the agent actively use its memory before every research session. This turns the agent from a static tool into a learning system.

**Ready for implementation via planloop following the agent-tooling-implementation-plan.md.**

---

**Version:** 2.0.0  
**Status:** Production-Ready Specification  
**Next Step:** Hand off to planloop for implementation
