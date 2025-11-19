import pytest
from pathlib import Path
import json
from datetime import datetime, timedelta

from honk.internal.memory.session_recorder import SessionRecorder, ResearchSession, SessionStatistics
from honk.internal.memory.strategy_manager import StrategyManager, Strategy, FailedPattern
from honk.internal.memory.knowledge_base import KnowledgeBase, Insight, TopicGuidance

@pytest.fixture
def memory_path(tmp_path) -> Path:
    """Fixture for a temporary memory storage path."""
    return tmp_path / "research-memory"

@pytest.fixture
def session_recorder(memory_path) -> SessionRecorder:
    """Fixture for a SessionRecorder instance."""
    return SessionRecorder(storage_path=memory_path)

@pytest.fixture
def strategy_manager(memory_path) -> StrategyManager:
    """Fixture for a StrategyManager instance."""
    return StrategyManager(storage_path=memory_path)

@pytest.fixture
def knowledge_base(memory_path) -> KnowledgeBase:
    """Fixture for a KnowledgeBase instance."""
    return KnowledgeBase(storage_path=memory_path)

class TestSessionRecorder:
    """Tests for the SessionRecorder."""

    def test_initialization(self, memory_path):
        """Test memory directory and files are created."""
        recorder = SessionRecorder(storage_path=memory_path)
        assert memory_path.exists()
        assert recorder.sessions_file.exists()
        data = json.loads(recorder.sessions_file.read_text())
        assert data == {"version": "1.0.0", "sessions": []}

    def test_record_session(self, session_recorder):
        """Test session is properly recorded to JSON."""
        session = ResearchSession(
            id="session-1",
            timestamp=datetime.now(),
            topic="Test Topic",
            mode="Quick Reference",
            searches_conducted=5,
            time_taken_minutes=30,
            quality_score=8,
            sources_used=3,
            what_worked=["Query A"],
            what_didnt_work=["Query B"],
            learnings=["Insight 1"]
        )
        session_recorder.record_session(session)
        data = json.loads(session_recorder.sessions_file.read_text())
        assert len(data['sessions']) == 1
        recorded_session = data['sessions'][0]
        assert recorded_session['topic'] == "Test Topic"
        assert recorded_session['quality_score'] == 8

    def test_get_sessions(self, session_recorder):
        """Test retrieving sessions with filters."""
        session1 = ResearchSession(id="s1", timestamp=datetime.now() - timedelta(days=1), topic="Python", mode="Deep Dive", searches_conducted=10, time_taken_minutes=60, quality_score=9, sources_used=5, what_worked=[], what_didnt_work=[], learnings=[])
        session2 = ResearchSession(id="s2", timestamp=datetime.now(), topic="JavaScript", mode="Quick Reference", searches_conducted=3, time_taken_minutes=15, quality_score=7, sources_used=2, what_worked=[], what_didnt_work=[], learnings=[])
        session3 = ResearchSession(id="s3", timestamp=datetime.now() - timedelta(days=2), topic="Python Advanced", mode="Deep Dive", searches_conducted=12, time_taken_minutes=90, quality_score=8, sources_used=7, what_worked=[], what_didnt_work=[], learnings=[])

        session_recorder.record_session(session1)
        session_recorder.record_session(session2)
        session_recorder.record_session(session3)

        sessions = session_recorder.get_sessions(topic_pattern="Python")
        assert len(sessions) == 2
        assert sessions[0].id == "s1" # Sorted by recency

        sessions = session_recorder.get_sessions(mode="Quick Reference")
        assert len(sessions) == 1
        assert sessions[0].id == "s2"

        sessions = session_recorder.get_sessions(min_quality=8)
        assert len(sessions) == 2
        assert sessions[0].id == "s1" # s2 has quality 7

    def test_find_similar_topics(self, session_recorder):
        """Test similar topic detection."""
        session1 = ResearchSession(id="s1", timestamp=datetime.now(), topic="Python Web Frameworks", mode="Deep Dive", searches_conducted=10, time_taken_minutes=60, quality_score=9, sources_used=5, what_worked=[], what_didnt_work=[], learnings=[])
        session2 = ResearchSession(id="s2", timestamp=datetime.now(), topic="JavaScript Frameworks", mode="Quick Reference", searches_conducted=3, time_taken_minutes=15, quality_score=7, sources_used=2, what_worked=[], what_didnt_work=[], learnings=[])
        session_recorder.record_session(session1)
        session_recorder.record_session(session2)

        similar = session_recorder.find_similar_topics("Python")
        assert len(similar) == 1
        assert similar[0].id == "s1"

    def test_get_statistics(self, session_recorder):
        """Test aggregate statistics calculation."""
        session1 = ResearchSession(id="s1", timestamp=datetime.now(), topic="A", mode="M", searches_conducted=1, time_taken_minutes=1, quality_score=10, sources_used=1, what_worked=[], what_didnt_work=[], learnings=[])
        session2 = ResearchSession(id="s2", timestamp=datetime.now(), topic="B", mode="M", searches_conducted=1, time_taken_minutes=1, quality_score=5, sources_used=1, what_worked=[], what_didnt_work=[], learnings=[])
        session_recorder.record_session(session1)
        session_recorder.record_session(session2)

        stats = session_recorder.get_statistics()
        assert stats.total_sessions == 2
        assert stats.avg_quality == 7.5

class TestStrategyManager:
    """Tests for the StrategyManager."""

    def test_initialization(self, memory_path):
        """Test memory directory and files are created."""
        manager = StrategyManager(storage_path=memory_path)
        assert memory_path.exists()
        assert manager.strategies_file.exists()
        data = json.loads(manager.strategies_file.read_text())
        assert data == {"version": "1.0.0", "successful_strategies": [], "failed_patterns": []}

    def test_record_success_new_strategy(self, strategy_manager):
        """Test recording a new successful strategy."""
        strategy_manager.record_success("Query Pattern A", "programming_language", "Use specific keywords")
        data = json.loads(strategy_manager.strategies_file.read_text())
        assert len(data['successful_strategies']) == 1
        s = data['successful_strategies'][0]
        assert s['pattern_name'] == "Query Pattern A"
        assert s['success_rate'] == 1.0
        assert s['times_used'] == 1

    def test_record_success_existing_strategy(self, strategy_manager):
        """Test updating an existing successful strategy."""
        strategy_manager.record_success("Query Pattern A", "programming_language", "Use specific keywords")
        strategy_manager.record_success("Query Pattern A", "programming_language", "Use specific keywords")
        data = json.loads(strategy_manager.strategies_file.read_text())
        assert len(data['successful_strategies']) == 1
        s = data['successful_strategies'][0]
        assert s['times_used'] == 2
        assert s['success_rate'] == 1.0 # Still 1.0 if all successes

    def test_record_failure_new_pattern(self, strategy_manager):
        """Test recording a new failed pattern."""
        strategy_manager.record_failure("Generic Query", "programming_language", "Too broad")
        data = json.loads(strategy_manager.strategies_file.read_text())
        assert len(data['failed_patterns']) == 1
        fp = data['failed_patterns'][0]
        assert fp['pattern_name'] == "Generic Query"
        assert fp['failure_rate'] == 1.0
        assert fp['times_tried'] == 1

    def test_record_failure_existing_pattern(self, strategy_manager):
        """Test updating an existing failed pattern."""
        strategy_manager.record_failure("Generic Query", "programming_language", "Too broad")
        strategy_manager.record_failure("Generic Query", "programming_language", "Too broad")
        data = json.loads(strategy_manager.strategies_file.read_text())
        assert len(data['failed_patterns']) == 1
        fp = data['failed_patterns'][0]
        assert fp['times_tried'] == 2
        assert fp['failure_rate'] == 1.0 # Still 1.0 if all failures

    def test_get_strategies_for_topic(self, strategy_manager):
        """Test retrieving strategies for a topic."""
        strategy_manager.record_success("S1", "lang", "Desc1")
        strategy_manager.record_success("S2", "lang", "Desc2")
        strategy_manager.update_confidence("S1", False) # Make S1 less confident

        strategies = strategy_manager.get_strategies_for_topic("lang", min_confidence=0.0)
        assert len(strategies) == 2
        assert strategies[0].pattern_name == "S2" # S2 should be higher confidence

    def test_get_patterns_to_avoid(self, strategy_manager):
        """Test retrieving failed patterns for a topic."""
        strategy_manager.record_failure("F1", "lang", "Why1")
        strategy_manager.record_failure("F2", "framework", "Why2")

        failed = strategy_manager.get_patterns_to_avoid("lang")
        assert len(failed) == 1
        assert failed[0].pattern_name == "F1"

    def test_update_confidence(self, strategy_manager):
        """Test updating confidence of a strategy."""
        strategy_manager.record_success("S1", "lang", "Desc1")
        strategy_manager.update_confidence("S1", False) # Fail once
        data = json.loads(strategy_manager.strategies_file.read_text())
        s = data['successful_strategies'][0]
        assert s['times_used'] == 2
        assert s['success_rate'] < 1.0 # Should have decreased

class TestKnowledgeBase:
    """Tests for the KnowledgeBase."""

    def test_initialization(self, memory_path):
        """Test memory directory and files are created."""
        kb = KnowledgeBase(storage_path=memory_path)
        assert memory_path.exists()
        assert kb.kb_file.exists()
        data = json.loads(kb.kb_file.read_text())
        assert data == {"version": "1.0.0", "topic_categories": {}, "insights": []}

    def test_add_insight(self, knowledge_base):
        """Test adding a new insight."""
        knowledge_base.add_insight("programming_language", "Python is great", ["session-1"])
        data = json.loads(knowledge_base.kb_file.read_text())
        assert len(data['insights']) == 1
        assert data['insights'][0]['insight'] == "Python is great"

    def test_get_insights_for_topic(self, knowledge_base):
        """Test retrieving insights for a topic."""
        knowledge_base.add_insight("programming_language", "Python is great", ["session-1"])
        knowledge_base.add_insight("framework", "Django is good", ["session-2"])
        
        insights = knowledge_base.get_insights_for_topic("programming_language")
        assert len(insights) == 1
        assert insights[0].insight == "Python is great"

    def test_update_topic_guidance(self, knowledge_base):
        """Test updating topic guidance."""
        knowledge_base.update_topic_guidance("programming_language", key_insight="Always check docs")
        data = json.loads(knowledge_base.kb_file.read_text())
        assert data['topic_categories']['programming_language']['key_insight'] == "Always check docs"

    def test_validate_insight(self, knowledge_base):
        """Test validating an insight."""
        knowledge_base.add_insight("programming_language", "Python is great", ["session-1"])
        insight_id = json.loads(knowledge_base.kb_file.read_text())['insights'][0]['id']
        
        knowledge_base.validate_insight(insight_id)
        data = json.loads(knowledge_base.kb_file.read_text())
        assert data['insights'][0]['validated_count'] == 1
        assert data['insights'][0]['confidence'] == "validated"
