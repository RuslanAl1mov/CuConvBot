import os
import telebot
from forex_python.converter import CurrencyRates, CurrencyCodes
import logging
from logging.handlers import RotatingFileHandler

# Настройка базового конфига логгера
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Создаем RotatingFileHandler для записи логов в файл logs.txt
log_file_handler = RotatingFileHandler('logs/bot_activity.log', maxBytes=1000000, backupCount=5, encoding='utf-8')
log_file_handler.setLevel(logging.INFO)
log_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Получаем логгер и добавляем к нему FileHandler
logger = logging.getLogger(__name__)
logger.addHandler(log_file_handler)

# Получаем токен из переменной окружения
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN environment variable is not set")
    raise ValueError("Не задан токен бота в переменной окружения TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

# Инициализируем объекты для работы с курсами валют.
currency_rates = CurrencyRates()
currency_codes = CurrencyCodes()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Отправляет приветственное сообщение и инструкции по использованию бота."""
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    bot.reply_to(message, "Привет! Я бот для конвертации валют.\n"
                          "Используй /convert для конвертации валют.\n"
                          "Используй /help для получения списка команд.")


@bot.message_handler(commands=['help'])
def send_help(message):
    """Предоставляет пользователю список доступных команд."""
    logger.info(f"Пользователь {message.from_user.id} запросил помощь")
    bot.reply_to(message, "/start - начать работу\n"
                          "/help - список команд\n"
                          "/convert X FROM TO - конвертировать сумму X из валюты FROM в валюту TO\n"
                          "Пример: /convert 100 USD EUR")


@bot.message_handler(commands=['convert'])
def convert_currency(message):
    """Конвертирует заданное количество одной валюты в другую."""
    logger.info(f"Пользователь {message.from_user.id} запрашивает конвертацию: {message.text}")
    args = message.text.split()[1:]
    if len(args) != 3:
        bot.reply_to(message, "Пожалуйста, используйте правильный формат: "
                              "/convert сумма исходная_валюта целевая_валюта\n"
                              "Пример: /convert 100 USD RUB")
        return

    amount, base_currency, target_currency = args
    try:
        amount = float(amount)
        converted_amount = currency_rates.convert(base_currency.upper(), target_currency.upper(), amount)
        symbol = currency_codes.get_symbol(target_currency.upper())
        bot.reply_to(message, f"{amount} {base_currency.upper()} = {symbol}{converted_amount:.2f} {target_currency.upper()}")
    except Exception as e:
        logger.error(f"Ошибка при конвертации для пользователя {message.from_user.id}: {str(e)}")
        bot.reply_to(message, f"Возможно такая Валюта не поддерживается этим API\n\nОшибка при конвертации: {str(e)}")


@bot.message_handler(func=lambda message: True)
def greeting_or_farewell(message):
    """
    Отвечает на простые текстовые сообщения с приветствием, прощанием или благодарностью
    в зависимости от контекста сообщения.
    """
    logger.info(f"Получено текстовое сообщение от {message.from_user.id}: {message.text}")

    # Примеры приветственных, прощальных фраз и фраз благодарности
    greetings = ['привет', 'здравствуй', 'добрый день', 'доброе утро', 'добрый вечер']
    farewells = ['пока', 'до свидания', 'до встречи', 'прощай']
    thanks = ['спасибо', 'благодарю', 'спс', 'большое спасибо']

    # Проверяем, содержит ли сообщение приветствие, прощание или благодарность
    message_text = message.text.lower()
    if any(greeting in message_text for greeting in greetings):
        logger.info(f"Отправлено приветствие пользователю {message.from_user.id}")
        bot.reply_to(message, "Привет! Чем могу помочь?")
    elif any(farewell in message_text for farewell in farewells):
        logger.info(f"Отправлено прощание пользователю {message.from_user.id}")
        bot.reply_to(message, "До свидания! Буду рад помочь вам в другой раз.")
    elif any(thank in message_text for thank in thanks):
        logger.info(f"Отправлена благодарность пользователю {message.from_user.id}")
        bot.reply_to(message, "Всегда пожалуйста! Если есть еще вопросы, не стесняйтесь обращаться.")
    else:
        logger.info(f"Сообщение от пользователя {message.from_user.id} не распознано")
        bot.reply_to(message, "Извините, я не понимаю эту команду. Используйте /help для списка команд.")


if __name__ == '__main__':
    logger.info("Запуск бота")
    try:
        bot.polling()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")
