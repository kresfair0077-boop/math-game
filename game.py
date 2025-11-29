"""
Логика генерации математических задач и управления игровыми сессиями.
"""
import random
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
from models import User, GameResult, Attempt
from config import Config
import db


@dataclass
class GameSession:
    """Структура для хранения состояния активной игровой сессии."""
    user_id: int
    current_question: str
    expected_answer: int
    score: int
    total_questions: int
    correct_answers: int
    end_time: datetime
    game_result: GameResult
    task: Optional[asyncio.Task] = None


class GameManager:
    """Менеджер игровых сессий и генерации задач."""
    
    def __init__(self):
        # Хранилище активных сессий: telegram_id -> GameSession
        self.active_sessions: Dict[int, GameSession] = {}
    
    def generate_question(self) -> Tuple[str, int]:
        """
        Генерирует математическую задачу и возвращает (текст задачи, правильный ответ).
        
        Правила:
        - Сложение/вычитание: результат 0-99
        - Умножение: результат <= 99
        - Деление: целочисленное, результат 0-11
        """
        operation = random.choice(['+', '-', '*', '/'])
        
        if operation == '+':
            # Сложение: a + b <= 99
            a = random.randint(0, 99)
            b = random.randint(0, 99 - a)
            answer = a + b
            question = f"{a} + {b}"
            
        elif operation == '-':
            # Вычитание: a >= b, результат >= 0
            a = random.randint(0, 99)
            b = random.randint(0, a)
            answer = a - b
            question = f"{a} - {b}"
            
        elif operation == '*':
            # Умножение: a * b <= 99
            max_a = 11
            a = random.randint(0, max_a)
            if a == 0:
                b = random.randint(0, 99)
            else:
                max_b = 99 // a
                b = random.randint(0, min(max_b, 9))
            answer = a * b
            question = f"{a} × {b}"
            
        else:  # operation == '/'
            # Деление: a / b, где a = b * k, k в 0..11, a <= 99
            b = random.randint(1, 9)
            max_k = min(11, 99 // b)
            k = random.randint(0, max_k)
            a = b * k
            answer = k
            question = f"{a} ÷ {b}"
        
        return question, answer
    
    async def start_game(
        self, 
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        end_callback = None
    ) -> Optional[GameSession]:
        """
        Запускает новую игровую сессию для пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            username: Username пользователя
            first_name: Имя пользователя
            last_name: Фамилия пользователя
            end_callback: Callback функция для вызова при завершении игры
            
        Returns:
            GameSession или None если уже есть активная сессия
        """
        # Проверяем, есть ли уже активная сессия
        if user_id in self.active_sessions:
            return None
        
        # Получаем или создаём пользователя
        user = db.get_or_create_user(user_id, username, first_name, last_name)
        
        # Создаём запись результата игры
        game_result = GameResult(user_telegram_id=user_id)
        
        # Генерируем первую задачу
        question, answer = self.generate_question()
        
        # Создаём сессию
        end_time = datetime.utcnow() + timedelta(seconds=Config.GAME_DURATION_SECONDS)
        session = GameSession(
            user_id=user_id,
            current_question=question,
            expected_answer=answer,
            score=0,
            total_questions=1,
            correct_answers=0,
            end_time=end_time,
            game_result=game_result
        )
        
        # Запускаем таймер
        if end_callback:
            task = asyncio.create_task(
                self._game_timer(user_id, end_time, end_callback)
            )
            session.task = task
        
        self.active_sessions[user_id] = session
        return session
    
    async def _game_timer(
        self, 
        user_id: int, 
        end_time: datetime, 
        callback
    ):
        """Таймер для завершения игры через 60 секунд."""
        wait_seconds = (end_time - datetime.utcnow()).total_seconds()
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        
        # Проверяем, что сессия ещё активна
        if user_id in self.active_sessions:
            await callback(user_id)
    
    def process_answer(
        self, 
        user_id: int, 
        user_answer: str
    ) -> Tuple[bool, Optional[str], Optional[int], Optional[bool]]:
        """
        Обрабатывает ответ пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            user_answer: Текст ответа от пользователя
            
        Returns:
            Tuple[is_valid_number, error_message, next_question, was_correct]
        """
        if user_id not in self.active_sessions:
            return False, "У тебя нет активной игры. Нажми «Начать игру» 🦄", None, None
        
        session = self.active_sessions[user_id]
        
        # Проверяем, не истекло ли время
        if datetime.utcnow() >= session.end_time:
            # Время истекло, завершаем игру
            self.end_game(user_id)
            return False, None, None, None
        
        # Сохраняем текущий вопрос и правильный ответ
        current_question = session.current_question
        current_expected_answer = session.expected_answer
        
        # Парсим ответ
        try:
            answer_int = int(user_answer.strip())
        except ValueError:
            return False, "Ой, похоже это не число 🫣 — пришли, пожалуйста, целый ответ (например 42).", None, None
        
        # Проверяем правильность
        was_correct = (answer_int == current_expected_answer)
        
        # Сохраняем попытку
        attempt = Attempt(
            question_text=current_question,
            expected_answer=current_expected_answer,
            user_answer=answer_int,
            correct=was_correct
        )
        session.game_result.attempts.append(attempt)
        
        # Обновляем счёт
        session.total_questions += 1
        if was_correct:
            session.correct_answers += 1
            session.score += 1
        
        # Генерируем следующий вопрос
        next_question, next_answer = self.generate_question()
        session.current_question = next_question
        session.expected_answer = next_answer
        
        return True, None, next_question, was_correct
    
    def end_game(self, user_id: int) -> Optional[GameResult]:
        """
        Завершает игровую сессию и сохраняет результат.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            GameResult или None если сессии не было
        """
        if user_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[user_id]
        
        # Отменяем таймер если он ещё работает
        if session.task and not session.task.done():
            session.task.cancel()
        
        # Обновляем результат игры
        session.game_result.score = session.score
        session.game_result.total_questions = session.total_questions
        session.game_result.correct_answers = session.correct_answers
        session.game_result.finished_at = datetime.utcnow().isoformat()
        
        # Сохраняем в файл
        db.save_game_result(session.game_result)
        
        game_result = session.game_result
        
        # Удаляем сессию
        del self.active_sessions[user_id]
        
        return game_result
    
    def get_session(self, user_id: int) -> Optional[GameSession]:
        """Получает активную сессию пользователя."""
        return self.active_sessions.get(user_id)
    
    def force_end_game(self, user_id: int):
        """Принудительно завершает игру (например, при старте новой)."""
        if user_id in self.active_sessions:
            self.end_game(user_id)
