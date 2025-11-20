from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class Strategy:
    """Successful research strategy pattern."""
    pattern_name: str
    topic_type: str                  # programming_language, framework, tool, etc.
    success_rate: float              # 0.0 to 1.0
    times_used: int
    confidence: str                  # low, medium, high
    description: str
    example_query: Optional[str] = None
    when_to_use: Optional[str] = None
    last_validated: Optional[datetime] = None

    def __post_init__(self):
        if self.last_validated is None:
            self.last_validated = datetime.now()

@dataclass
class FailedPattern:
    """Failed strategy pattern (anti-pattern)."""
    pattern_name: str
    topic_type: str
    failure_rate: float
    times_tried: int
    why_failed: str
    better_alternative: Optional[str] = None

class StrategyManager:
    """Manages research strategies and patterns."""
    
    def __init__(self, storage_path: Path = Path.home() / ".copilot" / "research-memory"):
        self.storage_path = storage_path
        self.strategies_file = storage_path / "strategies.json"
        self._ensure_storage()
        self._schema = self._load_schema()

    def _ensure_storage(self):
        """Ensures the memory storage directory and file exist."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        if not self.strategies_file.exists():
            with open(self.strategies_file, 'w') as f:
                json.dump({"version": "1.0.0", "successful_strategies": [], "failed_patterns": []}, f, indent=2)

    def _load_schema(self) -> Dict[str, Any]:
        """Loads the JSON schema for research strategies."""
        schema_path = Path(__file__).parent.parent.parent.parent.parent / "schemas" / "research-strategy.v1.json"
        with open(schema_path, 'r') as f:
            return json.load(f)

    def _read_strategies_data(self) -> Dict[str, Any]:
        """Reads the raw strategies data from the JSON file."""
        with open(self.strategies_file, 'r') as f:
            return json.load(f)

    def _write_strategies_data(self, data: Dict[str, Any]):
        """Writes the raw strategies data to the JSON file."""
        with open(self.strategies_file, 'w') as f:
            json.dump(data, f, indent=2)

    def record_success(
        self,
        pattern_name: str,
        topic_type: str,
        description: str,
        example_query: Optional[str] = None,
        context: Optional[str] = None
    ) -> None:
        """Record a successful strategy pattern."""
        data = self._read_strategies_data()
        
        # Find existing strategy or create new one
        strategy_found = False
        for s in data['successful_strategies']:
            if s['pattern_name'] == pattern_name and s['topic_type'] == topic_type:
                s['times_used'] += 1
                s['success_rate'] = (s['success_rate'] * (s['times_used'] - 1) + 1) / s['times_used'] # Simple update
                s['last_validated'] = datetime.now().isoformat()
                # Update confidence based on success_rate
                if s['success_rate'] > 0.9:
                    s['confidence'] = 'high'
                elif s['success_rate'] > 0.6:
                    s['confidence'] = 'medium'
                else:
                    s['confidence'] = 'low'
                strategy_found = True
                break
        
        if not strategy_found:
            new_strategy = Strategy(
                pattern_name=pattern_name,
                topic_type=topic_type,
                success_rate=1.0,
                times_used=1,
                confidence='high',
                description=description,
                example_query=example_query,
                when_to_use=context,
                last_validated=datetime.now()
            )
            new_strategy_dict = asdict(new_strategy)
            new_strategy_dict['last_validated'] = new_strategy.last_validated.isoformat() if new_strategy.last_validated else None  # type: ignore[union-attr]
            data['successful_strategies'].append(new_strategy_dict)
        
        self._write_strategies_data(data)
    
    def record_failure(
        self,
        pattern_name: str,
        topic_type: str,
        why_failed: str,
        better_alternative: Optional[str] = None
    ) -> None:
        """Record a failed strategy pattern."""
        data = self._read_strategies_data()

        # Find existing failed pattern or create new one
        failed_pattern_found = False
        for fp in data['failed_patterns']:
            if fp['pattern_name'] == pattern_name and fp['topic_type'] == topic_type:
                fp['times_tried'] += 1
                fp['failure_rate'] = (fp['failure_rate'] * (fp['times_tried'] - 1) + 1) / fp['times_tried'] # Simple update
                failed_pattern_found = True
                break
        
        if not failed_pattern_found:
            new_failed_pattern = FailedPattern(
                pattern_name=pattern_name,
                topic_type=topic_type,
                failure_rate=1.0,
                times_tried=1,
                why_failed=why_failed,
                better_alternative=better_alternative
            )
            data['failed_patterns'].append(asdict(new_failed_pattern))
        
        self._write_strategies_data(data)
    
    def get_strategies_for_topic(
        self,
        topic_type: str,
        min_confidence: float = 0.7
    ) -> List[Strategy]:
        """Get recommended strategies for a topic type."""
        data = self._read_strategies_data()
        strategies = []
        for s_dict in data['successful_strategies']:
            if s_dict['topic_type'] == topic_type and s_dict['success_rate'] >= min_confidence:
                strategies.append(Strategy(
                    pattern_name=s_dict['pattern_name'],
                    topic_type=s_dict['topic_type'],
                    success_rate=s_dict['success_rate'],
                    times_used=s_dict['times_used'],
                    confidence=s_dict['confidence'],
                    description=s_dict['description'],
                    example_query=s_dict.get('example_query'),
                    when_to_use=s_dict.get('when_to_use'),
                    last_validated=datetime.fromisoformat(s_dict['last_validated']) if s_dict.get('last_validated') else None
                ))
        strategies.sort(key=lambda s: s.success_rate, reverse=True)
        return strategies
    
    def get_patterns_to_avoid(self, topic_type: str) -> List[FailedPattern]:
        """Get patterns that have failed for this topic type."""
        data = self._read_strategies_data()
        failed_patterns = []
        for fp_dict in data['failed_patterns']:
            if fp_dict['topic_type'] == topic_type:
                failed_patterns.append(FailedPattern(
                    pattern_name=fp_dict['pattern_name'],
                    topic_type=fp_dict['topic_type'],
                    failure_rate=fp_dict['failure_rate'],
                    times_tried=fp_dict['times_tried'],
                    why_failed=fp_dict['why_failed'],
                    better_alternative=fp_dict.get('better_alternative')
                ))
        failed_patterns.sort(key=lambda fp: fp.failure_rate, reverse=True)
        return failed_patterns
    
    def update_confidence(self, pattern_name: str, success: bool) -> None:
        """Update confidence score based on new usage."""
        data = self._read_strategies_data()
        
        # Update successful strategies
        for s in data['successful_strategies']:
            if s['pattern_name'] == pattern_name:
                s['times_used'] += 1
                if success:
                    s['success_rate'] = (s['success_rate'] * (s['times_used'] - 1) + 1) / s['times_used']
                else:
                    s['success_rate'] = (s['success_rate'] * (s['times_used'] - 1)) / s['times_used']
                
                if s['success_rate'] > 0.9:
                    s['confidence'] = 'high'
                elif s['success_rate'] > 0.6:
                    s['confidence'] = 'medium'
                else:
                    s['confidence'] = 'low'
                s['last_validated'] = datetime.now().isoformat()
                break
        
        # Update failed patterns (if applicable, though typically success/failure are distinct)
        # This part might need more nuanced logic depending on how patterns are defined
        
        self._write_strategies_data(data)
