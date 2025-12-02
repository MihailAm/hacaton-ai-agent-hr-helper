"""Основной файл бота. Запускает приложение и регистрирует обработчики"""

from loguru import logger
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from tg_bot.handlers import commands, messages

TOKEN = "8344673772:AAHiHAZPZSsP_8SB5ryWm701RAK4TS4pfEo"


def setup_handlers(application: Application):
    """Регистрирует все обработчики команд и сообщений."""
    application.add_handler(CommandHandler("start", commands.start_command))
    application.add_handler(CommandHandler("help", commands.help_command))

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        messages.handle_text_message
    ))

    logger.info("Обработчики зарегистрированы")


def main():
    """Основная функция запуска бота."""
    print("=" * 50)
    print("🤖 ЗАПУСК TELEGRAM БОТА ДЛЯ ПРИЁМА РЕЗЮМЕ")
    print("=" * 50)

    try:
        application = Application.builder().token(TOKEN).build()

        setup_handlers(application)

        print(f"✅ Токен загружен: {'*' * 20}{TOKEN[-5:]}")
        print("🚀 Бот запущен и готов к работе!")
        print("=" * 50)
        print("Нажми Ctrl+C для остановки")
        print("=" * 50)

        application.run_polling(allowed_updates=None)

    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")


if __name__ == "__main__":
    main()
