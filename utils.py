"""
Вспомогательные функции для бота.
"""
import logging
import csv
import io
from typing import Optional, List
from datetime import datetime
import db
from models import User, GameResult

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def format_leaderboard(leaderboard_data: list) -> str:
    """
    Форматирует данные таблицы лидеров в красивый текст.
    
    Args:
        leaderboard_data: Список кортежей (username, best_score, total_games)
        
    Returns:
        Отформатированная строка с таблицей лидеров
    """
    if not leaderboard_data:
        return "🏆 Таблица лидеров пуста. Стань первым!"
    
    text = "🏆 **Топ-10 игроков:**\n\n"
    text += "```\n"
    text += f"{'№':<4} {'Игрок':<20} {'Лучший':<10} {'Игр':<6}\n"
    text += "-" * 42 + "\n"
    
    for idx, (username, best_score, total_games) in enumerate(leaderboard_data, 1):
        name = username or "Без имени"
        if len(name) > 18:
            name = name[:15] + "..."
        text += f"{idx:<4} {name:<20} {best_score:<10} {total_games:<6}\n"
    
    text += "```"
    return text


def get_leaderboard(limit: int = 10) -> list:
    """
    Получает топ игроков по лучшему результату.
    
    Args:
        limit: Количество игроков в топе
        
    Returns:
        Список кортежей (username, best_score, total_games)
    """
    all_results = db.get_all_game_results()
    all_users = db.get_all_users()
    
    # Создаём словарь пользователей для быстрого доступа
    users_dict = {user.telegram_id: user for user in all_users}
    
    # Собираем статистику по пользователям
    user_stats = {}
    for result in all_results:
        user_id = result.user_telegram_id
        if user_id not in user_stats:
            user_stats[user_id] = {
                'best_score': 0,
                'total_games': 0
            }
        user_stats[user_id]['best_score'] = max(
            user_stats[user_id]['best_score'], 
            result.score
        )
        user_stats[user_id]['total_games'] += 1
    
    # Формируем список для сортировки
    leaderboard = []
    for user_id, stats in user_stats.items():
        user = users_dict.get(user_id)
        username = (user.username if user else None) or (user.first_name if user else None) or "Без имени"
        leaderboard.append((
            username,
            stats['best_score'],
            stats['total_games']
        ))
    
    # Сортируем по лучшему результату, затем по количеству игр
    leaderboard.sort(key=lambda x: (-x[1], -x[2]))
    
    return leaderboard[:limit]


def format_user_stats(stats: dict) -> str:
    """Форматирует статистику пользователя в текст."""
    user = stats['user']
    name = user.username or user.first_name or "Игрок"
    
    text = f"📊 **Статистика {name}:**\n\n"
    text += f"🎮 Всего игр: {stats['total_games']}\n"
    text += f"⭐ Лучший результат: {stats['best_score']}\n"
    text += f"📈 Средний результат: {stats['avg_score']:.1f}\n"
    
    if stats['total_questions'] > 0:
        accuracy = (stats['total_correct'] / stats['total_questions']) * 100
        text += f"🎯 Точность: {accuracy:.1f}%\n"
        text += f"✅ Правильных ответов: {stats['total_correct']} из {stats['total_questions']}\n"
    
    return text


def export_results_to_csv() -> str:
    """
    Экспортирует все результаты игр в CSV формат.
    
    Returns:
        CSV строка с результатами
    """
    all_results = db.get_all_game_results()
    all_users = db.get_all_users()
    
    # Создаём словарь пользователей
    users_dict = {user.telegram_id: user for user in all_users}
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow([
        'Telegram ID', 'Username', 'First Name', 
        'Score', 'Total Questions', 'Correct Answers',
        'Started At', 'Finished At'
    ])
    
    # Данные
    for result in all_results:
        user = users_dict.get(result.user_telegram_id)
        writer.writerow([
            result.user_telegram_id,
            user.username if user else '',
            user.first_name if user else '',
            result.score,
            result.total_questions,
            result.correct_answers,
            result.started_at,
            result.finished_at or ''
        ])
    
    return output.getvalue()
