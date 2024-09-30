# system imports
import logging
import datetime
import json

# Izzy imports
from .exchange import Exchange

# Telegram imports
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext, MessageHandler, filters, CallbackQueryHandler

# Database imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.models import Base, User, ChatGroup, Symbol

from .notification_manager import NotificationManager
from .user_manager import UserManager
from .symbol_manager import SymbolManager
from .config import Config

class IzzyBot:
    def __init__(self, config: Config, engine):
        self.config = config
        self.logger = None
        self.setup_logging()
        self.logger.info("Logging setup completed")

        self.logger.info("Initializing application")
        self.application = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
        self.logger.info("Application initialized")

        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)
        self.logger.info("Session maker created")

        self.create_tables()
        self.logger.info("Database tables created")
        
        # Initialize managers and exchange
        self.logger.info("Initializing managers")
        self.user_manager = UserManager(self.Session)
        self.symbol_manager = SymbolManager(self.Session)
        self.exchange = Exchange(self.symbol_manager, self.config.BYBIT_API_KEY, self.config.BYBIT_API_SECRET)
        self.notification_manager = NotificationManager(self.exchange, self.Session)
        self.logger.info("Managers initialized")

        # Add handlers after initializing all components
        self.logger.info("Adding handlers")
        self.add_handlers()
        self.logger.info("Handlers added")

    def setup_logging(self):
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.user_manager.update_user_info(update)
        await update.message.reply_text(
            "Нажмите кнопку «Настроить параметры» для настройки бота",
            reply_markup=ReplyKeyboardMarkup.from_button(
                KeyboardButton(text="Настроить параметры", web_app=WebAppInfo(url="https://izzy.averkov.net"))
            ),
        )

    async def web_app_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        data = json.loads(update.effective_message.web_app_data.data)
        print(data)
        self.user_manager.update_user_info(update)
        self.logger.warn(f"Received web app data")
        await update.message.reply_text("Настройки сохранены")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.user_manager.update_user_info(update)
        await update.message.reply_text("Здесь будет краткая справка по боту")

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.user_manager.update_user_info(update)

    async def common_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.user_manager.update_user_info(update)

    async def hour_handler(self, context: CallbackContext) -> None:
        message = self.user_manager.get_registered_users()
        #await context.bot.send_message(84036596, message)

    async def day_handler(self, context: CallbackContext) -> None:
        message = self.user_manager.get_registered_users()
        await context.bot.send_message(84036596, message)

    async def minute_handler(self, context: CallbackContext) -> None:
        self.logger.info("Minute handler called")
        self.exchange.update_markets()
        await self.notification_manager.check_and_send_notifications(context)
        self.logger.info("Minute handler completed")

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

    def run(self):
        self.logger.info("Starting bot")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        self.logger.info("Bot stopped")

    def get_symbols(self) -> list:
        return self.symbol_manager.get_symbols()

    async def chart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.user_manager.update_user_info(update)
        symbols = self.symbol_manager.get_symbols()
        keyboard = [
            [
                InlineKeyboardButton(f"{symbol} (15m)", callback_data=f"chart_symbol_{symbol}_15m"),
                InlineKeyboardButton(f"{symbol} (4h)", callback_data=f"chart_symbol_{symbol}_4h")
            ]
            for symbol in symbols
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите символ и временной интервал для построения графика:", reply_markup=reply_markup)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        if query.data.startswith("chart_symbol_"):
            parts = query.data.split("_")
            if len(parts) >= 4:
                symbol, timeframe = parts[2], parts[3]
                try:
                    market = self.exchange.get_market(symbol)
                    if market is None:
                        await query.message.reply_text(f"Извините, не удалось найти рынок для {symbol}.")
                        return

                    chart = market.get_chart(timeframe)
                    if chart is None:
                        await query.message.reply_text(f"Извините, не удалось создать график для {symbol} ({timeframe}). Попробуйте позже.")
                    else:
                        chart_bytes = chart.save()
                        await query.message.reply_photo(photo=chart_bytes, caption=f"График для {symbol} ({timeframe})")
                except Exception as e:
                    self.logger.exception(f"Error creating chart for symbol {symbol}, timeframe: {timeframe}")
                    await query.message.reply_text(f"Произошла ошибка при создании графика для {symbol} ({timeframe}): {str(e)}")
            else:
                await query.message.reply_text("Извините, произошла ошибка при обработке запроса.")

    async def admin_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("У вас нет прав для выполнения этой команды.")
            return
        users = self.user_manager.get_registered_users()
        await update.message.reply_text(users)

    async def admin_symbols(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("У вас нет прав для выполнения этой команды.")
            return
        symbols = self.symbol_manager.get_symbols()
        await update.message.reply_text(f"Текущие символы: {', '.join(symbols)}")

    async def admin_add_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("У вас нет прав для выполнения этой команды.")
            return
        if len(context.args) != 2:
            await update.message.reply_text("Использование: /add_symbol <symbol> <icon_class>")
            return
        symbol, icon_class = context.args
        self.symbol_manager.add_symbol(symbol, icon_class)
        await update.message.reply_text(f"Символ {symbol} добавлен.")

    def is_admin(self, user_id: int) -> bool:
        # Implement admin check logic
        return user_id == self.config.ADMIN_USER_ID


    def add_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, self.web_app_data))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo))
        
        # Add job queue handlers
        job_queue = self.application.job_queue
        minute_job = job_queue.run_repeating(self.minute_handler, interval=60, first=1)
        hour_job = job_queue.run_repeating(self.hour_handler, interval=3600, first=1)
        day_job = job_queue.run_daily(self.day_handler, time=datetime.time(hour=0, minute=0, second=0))
        
        self.logger.info(f"Minute job scheduled: {minute_job}")
        self.logger.info(f"Hour job scheduled: {hour_job}")
        self.logger.info(f"Day job scheduled: {day_job}")
        
        self.application.add_handler(CommandHandler("chart", self.chart_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

        # Add admin handlers
        self.application.add_handler(CommandHandler("admin_users", self.admin_users))
        self.application.add_handler(CommandHandler("admin_symbols", self.admin_symbols))
        self.application.add_handler(CommandHandler("admin_add_symbol", self.admin_add_symbol))
