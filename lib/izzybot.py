# system imports
import logging
import time
import datetime
import json

# Izzy imports
from .exchange import Exchange

# Telegram imports
from telegram import Update, Chat, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext, MessageHandler, filters

# Database imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.models import Base, User, ChatGroup, Symbol

class IzzyBot:
    def __init__(self, settings, engine):
        self.settings = settings
        self.logger = None
        self.setup_logging()

        token = self.settings.TELEGRAM_BOT_TOKEN
        self.application = Application.builder().token(token).build()

        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)

        self.create_tables()
        self.add_handlers()

        # Initialize exchange after DB initialization
        self.exchange = Exchange(self, self.settings.BYBIT_API_KEY, self.settings.BYBIT_API_SECRET)

    def setup_logging(self):
        logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        self.logger = logging.getLogger(__name__)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def update_user_info(self, update: Update) -> None:
        now = int(time.time())
        chat = update.effective_chat
        is_group = (chat.type == Chat.GROUP or chat.type == Chat.SUPERGROUP)

        session = self.Session()

        try:
            if is_group:
                self.logger.info(f"Updating chat info for {chat.title} ({chat.id})")
                chat_group = session.get(ChatGroup, chat.id)
                if chat_group:
                    chat_group.title = chat.title
                else:
                    chat_group = ChatGroup(id=chat.id, title=chat.title)
                    session.add(chat_group)
            else:
                user = update.effective_user
                self.logger.info(f"Updating user info for {user.first_name} {user.last_name} ({user.id})")
                db_user = session.get(User, user.id)
                if db_user:
                    db_user.first_name = user.first_name
                    db_user.last_name = user.last_name
                    db_user.nickname = user.username
                    db_user.is_premium = user.is_premium
                    db_user.last_seen = now
                else:
                    db_user = User(id=user.id, first_name=user.first_name, last_name=user.last_name,
                                   nickname=user.username, is_premium=user.is_premium, last_seen=now)
                    session.add(db_user)

            session.commit()
        finally:
            session.close()

    def add_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, self.web_app_data))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo))
        self.application.add_handler(MessageHandler(filters.ALL, self.common_handler))
        self.application.job_queue.run_repeating(self.minute_handler, interval=60, name="minute_job")
        self.application.job_queue.run_repeating(self.hour_handler, interval=120, name="hour_job")
        self.application.job_queue.run_daily(self.day_handler, time=datetime.time(18, 0), name="day_job")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.update_user_info(update)
        await update.message.reply_text(
            "Нажмите кнопку «Настроить параметры» для настройки бота",
            reply_markup=ReplyKeyboardMarkup.from_button(
                KeyboardButton(text="Настроить параметры", web_app=WebAppInfo(url="https://izzy.averkov.net"))
            ),
        )

    async def web_app_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        data = json.loads(update.effective_message.web_app_data.data)
        print(data)
        self.update_user_info(update)
        self.logger.warn(f"Received web app data")
        await update.message.reply_text("Настройки сохранены")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.update_user_info(update)
        await update.message.reply_text("Здесь будет краткая справка по боту")

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
        await self.check_and_send_notifications(context)

    async def check_and_send_notifications(self, context: CallbackContext):
        session = self.Session()
        try:
            current_time = int(time.time())
            users = session.query(User).all()
            
            for symbol, market in self.exchange.markets.items():
                status_15m = market.is_price_in_extreme_range('15m')
                status_4h = market.is_price_in_extreme_range('4h')
                
                if status_15m != 'normal' or status_4h != 'normal':
                    for user in users:
                        last_notifications = user.last_notifications or {}
                        last_notification_time = last_notifications.get(symbol, 0)
                        
                        if current_time - last_notification_time > user.notification_timeout:
                            message = self.create_notification_message(symbol, status_15m, status_4h)
                            await context.bot.send_message(user.id, message)
                            
                            last_notifications[symbol] = current_time
                            user.last_notifications = last_notifications
                            session.commit()
        finally:
            session.close()

    def create_notification_message(self, symbol, status_15m, status_4h):
        message = f"Уведомление по {symbol}:\n"
        if status_15m != 'normal':
            message += f"15-минутный график: цена в {'верхнем' if status_15m == 'high' else 'нижнем'} диапазоне\n"
        if status_4h != 'normal':
            message += f"4-часовой график: цена в {'верхнем' if status_4h == 'high' else 'нижнем'} диапазоне\n"
        return message

    def get_registered_users(self) -> str:
        session = self.Session()
        try:
            users = session.query(User).all()
            message = f"Зарегистрированные пользователи:\n"
            for user in users:
                premium_str = " ✅" if user.is_premium else ''
                message += f"{user.first_name} {user.last_name} (@{user.nickname}){premium_str}\n"
            return message
        finally:
            session.close()

    def get_symbols(self) -> list:
        session = self.Session()
        try:
            symbols = session.query(Symbol.symbol).all()
            return [symbol[0] for symbol in symbols]
        finally:
            session.close()

    def run(self):
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
