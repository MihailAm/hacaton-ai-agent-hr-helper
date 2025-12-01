"""Обработчики текстовых сообщений от пользователей"""

from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает ВСЕ текстовые сообщения от пользователя.
    Считает, что любое сообщение — это резюме
    """
    user = update.effective_user
    text = update.message.text.strip()

    logger.info(f"Received message from {user.id} ({user.username}): {text[:50]}...")

    if len(text) < 50:
        await update.message.reply_text(
            "❌ *Сообщение слишком короткое для резюме.*\n\n"
            "Пожалуйста, отправь полное резюме.\n"
            "Минимальная длина — *50 символов*.\n"
            "Текущая длина: {len(text)} символов.\n\n"
            "Используй /help для примера формата.",
            parse_mode="Markdown"
        )
        return

    processing_msg = await update.message.reply_text(
        "📥 *Получил твоё резюме...*\n"
        "Сохраняю и обрабатываю...",
        parse_mode="Markdown"
    )

    try:
        logger.info(f'text for messages: {text}')
        # TODO: Формируем ответ тут
        success_text = f"""
                        ✅ *Резюме успешно сохранено!*
                        *🔄 Что дальше:*
                        ФОРМИРУЕМ ОТВЕТ
                        """

        await processing_msg.edit_text(
            success_text,
            parse_mode="Markdown"
        )

        logger.info(f"Resume saved for user {user.id}: {['filename']}")

    except Exception as e:
        logger.error(f"Error saving resume for user {user.id}: {e}")

        await processing_msg.edit_text(
            "❌ *Произошла ошибка при сохранении резюме.*\n\n"
            "Попробуй отправить резюме ещё раз через пару минут.\n"
            "Если ошибка повторится — свяжись с администратором.",
            parse_mode="Markdown"
        )
