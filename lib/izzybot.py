# system imports
import logging
import sqlite3
import time
import datetime

# Izzy imports
from .exchange import Exchange

# Telegram imports
from telegram import Update, Chat, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext, MessageHandler, filters


class IzzyBot:
    def __init__(self, settings):
        self.settings = settings
        self.logger = None
        self.setup_logging()

        token = settings.TELEGRAM_BOT_TOKEN
        self.application = Application.builder().token(token).build()
        self.database = sqlite3.connect(settings.DATABASE)

        self.create_tables()
        self.add_handlers()

        # Биржу инициализируем только после инициализации БД
        self.exchange = Exchange(self, settings.BYBIT_API_KEY, settings.BYBIT_API_SECRET)

    def setup_logging(self):
        logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        self.logger = logging.getLogger(__name__)

    def create_tables(self):
        cursor = self.database.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT, 
        nickname TEXT, is_premium BOOLEAN, last_seen INTEGER)''')
        cursor.execute('CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY, title TEXT)')
        cursor.execute('''CREATE TABLE IF NOT EXISTS symbols (symbol TEXT PRIMARY KEY,
        last_mark_price REAL, monitor_oi BOOLEAN DEFAULT FALSE, oi_threshold REAL DEFAULT 0.0, monitor_fvg BOOLEAN
        DEFAULT FALSE, fvg_threshold REAL DEFAULT 0.0)''')
        self.database.commit()

    def update_user_info(self, update: Update) -> None:
        now = int(time.time())
        chat = update.effective_chat
        is_group = (chat.type == Chat.GROUP or chat.type == Chat.SUPERGROUP)

        cursor = self.database.cursor()

        if is_group:
            self.logger.info(f"Updating chat info for {chat.title} ({chat.id})")
            cursor.execute(
                "REPLACE INTO chats (id, title) VALUES (?, ?)",
                (chat.id, chat.title),
            )
        else:
            user = update.effective_user
            self.logger.info(f"Updating user info for {user.first_name} {user.last_name} ({user.id})")
            cursor.execute(
                "REPLACE INTO users (id, first_name, last_name, nickname, is_premium, last_seen) VALUES (?, ?, ?, ?, "
                "?, ?)",
                (user.id, user.first_name, user.last_name, user.username, user.is_premium, now),
            )

        self.database.commit()

    def add_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo))
        self.application.add_handler(MessageHandler(filters.ALL, self.common_handler))
        self.application.job_queue.run_repeating(self.minute_handler, interval=60, name="minute_job")
        self.application.job_queue.run_repeating(self.hour_handler, interval=120, name="hour_job")
        self.application.job_queue.run_daily(self.day_handler, time=datetime.time(18, 0), name="day_job")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.update_user_info(update)
        await update.message.reply_html(rf"Тадам!")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.update_user_info(update)
        await update.message.reply_text("Здесь будет краткая справка по боту.\n")

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.update_user_info(update)

    async def common_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.update_user_info(update)

    async def hour_handler(self, context: CallbackContext) -> None:
        message = self.get_registered_users()
        #await context.bot.send_message(84036596, message)

    async def day_handler(self, context: CallbackContext) -> None:
        message = self.get_registered_users()
        await context.bot.send_message(84036596, message)

    async def minute_handler(self, context: CallbackContext) -> None:
        self.exchange.update_markets()

    def get_registered_users(self) -> str:
        cursor = self.database.cursor()
        cursor.execute("SELECT nickname, first_name, last_name, is_premium FROM users")
        message = f"Зарегистрированные пользователи:\n"
        for nickname, first_name, last_name, is_premium in cursor.fetchall():
            premium_str = " ✅" if is_premium else ''
            message += f"{first_name} {last_name} (@{nickname}){premium_str}\n"
        cursor.close()
        return message

    def get_symbols(self) -> list:
        cursor = self.database.cursor()
        cursor.execute("SELECT symbol FROM symbols")
        return [row[0] for row in cursor.fetchall()]

    def run(self):
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)