"""
Модели данных для хранения в JSON файле.
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List


@dataclass
class User:
    """Модель пользователя."""
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
    
    def to_dict(self):
        """Преобразует объект в словарь для JSON."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        """Создаёт объект из словаря."""
        return cls(**data)


@dataclass
class Attempt:
    """Модель попытки ответа на вопрос."""
    question_text: str
    expected_answer: int
    user_answer: Optional[int]
    correct: bool
    answered_at: str = None
    
    def __post_init__(self):
        if self.answered_at is None:
            self.answered_at = datetime.utcnow().isoformat()
    
    def to_dict(self):
        """Преобразует объект в словарь для JSON."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        """Создаёт объект из словаря."""
        return cls(**data)


@dataclass
class GameResult:
    """Модель результата игрового раунда."""
    user_telegram_id: int
    score: int = 0
    total_questions: int = 0
    correct_answers: int = 0
    started_at: str = None
    finished_at: Optional[str] = None
    attempts: List[Attempt] = None
    
    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.utcnow().isoformat()
        if self.attempts is None:
            self.attempts = []
    
    def to_dict(self):
        """Преобразует объект в словарь для JSON."""
        data = asdict(self)
        data['attempts'] = [attempt.to_dict() if hasattr(attempt, 'to_dict') else attempt for attempt in self.attempts]
        return data
    
    @classmethod
    def from_dict(cls, data: dict):
        """Создаёт объект из словаря."""
        attempts_data = data.pop('attempts', [])
        obj = cls(**data)
        obj.attempts = [Attempt.from_dict(a) if isinstance(a, dict) else a for a in attempts_data]
        return obj
