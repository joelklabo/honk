from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from jsonschema import validate, ValidationError

@dataclass
class ResearchSession:
    """Single research session record."""
    id: str
    timestamp: datetime
    topic: str
    mode: str
    searches_conducted: int
    time_taken_minutes: int
    quality_score: int
    sources_used: int
    what_worked: List[str]
    what_didnt_work: List[str]
    learnings: List[str]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class SessionStatistics:
    """Aggregate statistics across all sessions."""
    def __init__(self, total_sessions: int = 0, avg_quality: float = 0.0, time_trends: str = "N/A"):
        self.total_sessions = total_sessions
        self.avg_quality = avg_quality
        self.time_trends = time_trends

class SessionRecorder:
    """Records research sessions for learning and improvement."""
    
    def __init__(self, storage_path: Path = Path.home() / ".copilot" / "research-memory"):
        self.storage_path = storage_path
        self.sessions_file = storage_path / "sessions.json"
        self._ensure_storage()
        self._schema = self._load_schema()

    def _ensure_storage(self):
        """Ensures the memory storage directory and file exist."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        if not self.sessions_file.exists():
            with open(self.sessions_file, 'w') as f:
                json.dump({"version": "1.0.0", "sessions": []}, f, indent=2)

    def _load_schema(self) -> Dict[str, Any]:
        """Loads the JSON schema for research sessions."""
        schema_path = Path(__file__).parent.parent.parent.parent.parent / "schemas" / "research-session.v1.json"
        with open(schema_path, 'r') as f:
            return json.load(f)

    def _read_sessions_data(self) -> Dict[str, Any]:
        """Reads the raw sessions data from the JSON file."""
        with open(self.sessions_file, 'r') as f:
            return json.load(f)

    def _write_sessions_data(self, data: Dict[str, Any]):
        """Writes the raw sessions data to the JSON file."""
        with open(self.sessions_file, 'w') as f:
            json.dump(data, f, indent=2)

    def record_session(self, session: ResearchSession) -> None:
        """Record a completed research session."""
        session_dict = asdict(session)
        # Convert datetime to ISO format string for JSON
        session_dict['timestamp'] = session.timestamp.isoformat()
        
        try:
            validate(instance=session_dict, schema=self._schema['properties']['sessions']['items'])
        except ValidationError as e:
            raise ValueError(f"Session data failed schema validation: {e.message}")

        data = self._read_sessions_data()
        data['sessions'].append(session_dict)
        self._write_sessions_data(data)
    
    def get_sessions(
        self,
        topic_pattern: Optional[str] = None,
        mode: Optional[str] = None,
        min_quality: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[ResearchSession]:
        """Retrieve past sessions matching criteria."""
        data = self._read_sessions_data()
        sessions = []
        for s_dict in data['sessions']:
            session = ResearchSession(
                id=s_dict['id'],
                timestamp=datetime.fromisoformat(s_dict['timestamp']),
                topic=s_dict['topic'],
                mode=s_dict['mode'],
                searches_conducted=s_dict.get('searches_conducted', 0),
                time_taken_minutes=s_dict.get('time_taken_minutes', 0),
                quality_score=s_dict['quality_score'],
                sources_used=s_dict.get('sources_used', 0),
                what_worked=s_dict.get('what_worked', []),
                what_didnt_work=s_dict.get('what_didnt_work', []),
                learnings=s_dict.get('learnings', []),
                metadata=s_dict.get('metadata', {})
            )
            
            match = True
            if topic_pattern and topic_pattern.lower() not in session.topic.lower():
                match = False
            if mode and mode.lower() != session.mode.lower():
                match = False
            if min_quality and session.quality_score < min_quality:
                match = False
            
            if match:
                sessions.append(session)
        
        # Sort by recency (newest first)
        sessions.sort(key=lambda s: s.timestamp, reverse=True)
        
        if limit:
            sessions = sessions[:limit]
            
        return sessions
    
    def find_similar_topics(self, topic: str) -> List[ResearchSession]:
        """Find past sessions on similar topics."""
        # Simple keyword matching for now, can be enhanced with semantic similarity later
        return self.get_sessions(topic_pattern=topic)
    
    def get_statistics(self) -> SessionStatistics:
        """Get aggregate statistics across all sessions."""
        sessions = self.get_sessions()
        total_sessions = len(sessions)
        
        if total_sessions == 0:
            return SessionStatistics()
            
        avg_quality = sum(s.quality_score for s in sessions) / total_sessions
        
        # Placeholder for more complex time trend analysis
        time_trends = "Improvement analysis not yet implemented" 
        
        return SessionStatistics(total_sessions, avg_quality, time_trends)
