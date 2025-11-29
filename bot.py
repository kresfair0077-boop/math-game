"""
Главный файл для запуска Telegram-бота Unicorn Math Game.
Использует long polling (без webhooks).
Хранит данные в JSON файле (data.json).
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from config import Config
from game import GameManager
from handlers import user_handlers, admin_handlers

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


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуй ещё раз или напиши /start"
            )
        except Exception:
            pass


def main():
    """Главная функция для запуска бота."""
    # Проверяем конфигурацию
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        return
    
    # Создаём приложение
    application = Application.builder().token(Config.TG_TOKEN).build()
    
    # Инициализируем игровой менеджер
    game_manager = GameManager()
    application.bot_data['game_manager'] = game_manager
    
    # Регистрируем обработчики команд для пользователей
    application.add_handler(CommandHandler("start", user_handlers.start_command))
    application.add_handler(CommandHandler("profile", user_handlers.profile_command))
    
    # Регистрируем обработчики команд для админа
    application.add_handler(CommandHandler("admin", admin_handlers.admin_command))
    application.add_handler(CommandHandler("stats", admin_handlers.stats_command))
    application.add_handler(CommandHandler("users", admin_handlers.users_command))
    application.add_handler(CommandHandler("user", admin_handlers.user_command))
    application.add_handler(CommandHandler("export_results", admin_handlers.export_results_command))
    application.add_handler(CommandHandler("leaderboard", admin_handlers.admin_leaderboard_command))
    
    # Регистрируем обработчики callback-кнопок
    application.add_handler(
        CallbackQueryHandler(
            user_handlers.start_game_callback,
            pattern="^start_game$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            user_handlers.leaderboard_callback,
            pattern="^leaderboard$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            user_handlers.my_profile_callback,
            pattern="^my_profile$"
        )
    )
    
    # Регистрируем обработчик текстовых сообщений (ответы на задачи)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            user_handlers.handle_message
        )
    )
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота через long polling
    logger.info("Запуск бота через long polling...")
    logger.info(f"Admin ID: {Config.ADMIN_ID}")
    logger.info("Данные хранятся в файле data.json")
    
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Остановка бота...")
    finally:
        logger.info("Бот остановлен")


if __name__ == "__main__":
    main()
