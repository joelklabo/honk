from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field

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
    examples: List[str] = field(default_factory=list)  # type: ignore[assignment]

    def __post_init__(self):
        if self.examples is None:
            self.examples = []

class KnowledgeBase:
    """Manages topic-specific knowledge and insights."""
    
    def __init__(self, storage_path: Path = Path.home() / ".copilot" / "research-memory"):
        self.storage_path = storage_path
        self.kb_file = storage_path / "knowledge-base.json"
        self._ensure_storage()
        self._schema = self._load_schema()

    def _ensure_storage(self):
        """Ensures the memory storage directory and file exist."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        if not self.kb_file.exists():
            with open(self.kb_file, 'w') as f:
                json.dump({"version": "1.0.0", "topic_categories": {}, "insights": []}, f, indent=2)

    def _load_schema(self) -> Dict[str, Any]:
        """Loads the JSON schema for the knowledge base."""
        schema_path = Path(__file__).parent.parent.parent.parent.parent / "schemas" / "knowledge-base.v1.json"
        with open(schema_path, 'r') as f:
            return json.load(f)

    def _read_kb_data(self) -> Dict[str, Any]:
        """Reads the raw knowledge base data from the JSON file."""
        with open(self.kb_file, 'r') as f:
            return json.load(f)

    def _write_kb_data(self, data: Dict[str, Any]):
        """Writes the raw knowledge base data to the JSON file."""
        with open(self.kb_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_insight(
        self,
        topic_category: str,
        insight_text: str,
        source_sessions: List[str],
        confidence: str = "provisional"
    ) -> None:
        """Add a new insight to the knowledge base."""
        data = self._read_kb_data()
        
        new_insight = Insight(
            id=f"insight-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            topic_category=topic_category,
            insight=insight_text,
            discovered=datetime.now(),
            validated_count=0,
            confidence=confidence,
            source_sessions=source_sessions
        )
        
        insight_dict = asdict(new_insight)
        insight_dict['discovered'] = new_insight.discovered.isoformat()

        # Basic check for duplicates
        if not any(i['insight'] == insight_dict['insight'] and i['topic_category'] == insight_dict['topic_category'] for i in data['insights']):
            data['insights'].append(insight_dict)
            self._write_kb_data(data)
    
    def get_insights_for_topic(self, topic_category: str) -> List[Insight]:
        """Get all insights for a topic category."""
        data = self._read_kb_data()
        insights = []
        for i_dict in data['insights']:
            if i_dict['topic_category'] == topic_category:
                insights.append(Insight(
                    id=i_dict['id'],
                    topic_category=i_dict['topic_category'],
                    insight=i_dict['insight'],
                    discovered=datetime.fromisoformat(i_dict['discovered']),
                    validated_count=i_dict['validated_count'],
                    confidence=i_dict['confidence'],
                    source_sessions=i_dict['source_sessions']
                ))
        insights.sort(key=lambda i: i.confidence, reverse=True) # Sort by confidence
        return insights
    
    def update_topic_guidance(
        self,
        topic_category: str,
        key_insight: Optional[str] = None,
        best_sources: Optional[List[str]] = None,
        avoid: Optional[List[str]] = None,
        search_template: Optional[str] = None
    ) -> None:
        """Update guidance for a topic category."""
        data = self._read_kb_data()
        
        if topic_category not in data['topic_categories']:
            data['topic_categories'][topic_category] = {}
            
        if key_insight:
            data['topic_categories'][topic_category]['key_insight'] = key_insight
        if best_sources:
            data['topic_categories'][topic_category]['best_sources'] = best_sources
        if avoid:
            data['topic_categories'][topic_category]['avoid'] = avoid
        if search_template:
            data['topic_categories'][topic_category]['search_template'] = search_template
            
        self._write_kb_data(data)
    
    def validate_insight(self, insight_id: str) -> None:
        """Promote insight from provisional to validated."""
        data = self._read_kb_data()
        for insight in data['insights']:
            if insight['id'] == insight_id:
                insight['validated_count'] += 1
                if insight['validated_count'] >= 3: # Example threshold
                    insight['confidence'] = 'high_confidence'
                elif insight['validated_count'] >= 1:
                    insight['confidence'] = 'validated'
                self._write_kb_data(data)
                return
        raise ValueError(f"Insight with ID {insight_id} not found.")
