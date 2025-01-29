import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
import requests

# Константы
YOUGILE_API_URL = "https://api.yougile.com/api-v2"
YOUGILE_API_KEY = "ваш_api_key_для_yougile"  # Замените на ваш API ключ
TELEGRAM_BOT_TOKEN = "ваш_telegram_bot_token"  # Замените на токен вашего Telegram-бота

# Состояния для ConversationHandler
SELECT_PRIORITY, TASK_DESCRIPTION = range(2)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Приветственное сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Подать задачу"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Я бот для создания задач в YouGile. Нажмите 'Подать задачу', чтобы начать.",
        reply_markup=reply_markup,
    )
    return SELECT_PRIORITY

# Выбор приоритета
async def select_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Критический", "Высокий"], ["Нормальный", "Низкий"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Выберите приоритет задачи:", reply_markup=reply_markup
    )
    return TASK_DESCRIPTION

# Создание задачи в YouGile
async def create_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text
    user_name = update.message.from_user.username or update.message.from_user.full_name

    # Получаем приоритет из контекста
    priority = context.user_data.get("priority", "normal")  # По умолчанию "normal"

    # Формируем данные для YouGile API
    task_data = {
        "title": f"Задача от @{user_name}",
        "description": description,
        "priority": priority,  # Передаем выбранный приоритет
        "status": "todo",  # Можно настроить статус по умолчанию
    }

    headers = {
        "Authorization": f"Bearer {YOUGILE_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(f"{YOUGILE_API_URL}/tasks", json=task_data, headers=headers)
        if response.status_code == 201:
            await update.message.reply_text(
                "Задача успешно создана в YouGile!", reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text("Произошла ошибка при создании задачи.")
            logger.error(f"YouGile API Error: {response.status_code}, {response.text}")
    except Exception as e:
        await update.message.reply_text("Не удалось подключиться к YouGile API.")
        logger.error(f"Exception: {e}")

    return ConversationHandler.END

# Обработка выбора приоритета
async def set_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    priority_map = {
        "Критический": "critical",
        "Высокий": "high",
        "Нормальный": "normal",
        "Низкий": "low",
    }
    selected_priority = update.message.text
    context.user_data["priority"] = priority_map.get(selected_priority, "normal")

    await update.message.reply_text(
        f"Вы выбрали приоритет: {selected_priority}. Введите описание задачи:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return TASK_DESCRIPTION

# Основная функция для запуска бота
def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_PRIORITY: [
                MessageHandler(filters.Regex("^Подать задачу$"), select_priority),
            ],
            TASK_DESCRIPTION: [
                MessageHandler(
                    filters.Regex("^(Критический|Высокий|Нормальный|Низкий)$"), set_priority
                ),
                MessageHandler(filters.TEXT & ~filters.COMMAND, create_task),
            ],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()