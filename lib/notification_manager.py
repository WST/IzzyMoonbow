import logging
import time
from telegram.ext import CallbackContext
from lib.models import User, NotificationHistory, Symbol
from .chart_generator import ChartGenerator
from sqlalchemy import and_

class NotificationManager:
    def __init__(self, exchange, session_maker):
        self.exchange = exchange
        self.Session = session_maker
        self.logger = logging.getLogger(__name__)
        self.chart_generator = ChartGenerator()

    async def check_and_send_notifications(self, context: CallbackContext):
        session = self.Session()
        try:
            current_time = int(time.time())
            users = session.query(User).all()
            
            for symbol in self.exchange.markets.keys():
                market = self.exchange.get_market(symbol)
                if market is None:
                    self.logger.error(f"Skipping notifications for invalid symbol: {symbol}")
                    continue
                
                status_15m = market.is_price_in_extreme_range('15m')
                status_4h = market.is_price_in_extreme_range('4h')
                
                for user in users:
                    if user.price_notifications:
                        if status_15m != 'normal' and self.should_send_notification(user, symbol, 'price', status_15m, '15m', current_time):
                            await self.send_price_notification(context, user, symbol, status_15m, '15m')
                            self.update_notification_history(session, user, symbol, 'price', status_15m, '15m', current_time)
                        
                        if status_4h != 'normal' and self.should_send_notification(user, symbol, 'price', status_4h, '4h', current_time):
                            await self.send_price_notification(context, user, symbol, status_4h, '4h')
                            self.update_notification_history(session, user, symbol, 'price', status_4h, '4h', current_time)
                    
                    # Add similar checks for FVG and OI notifications
            
            session.commit()
        finally:
            session.close()

    def should_send_notification(self, user, symbol, notification_type, status, timeframe, current_time):
        last_notification = self.Session().query(NotificationHistory).filter(
            NotificationHistory.user_id == user.id,
            NotificationHistory.symbol == symbol,
            NotificationHistory.notification_type == notification_type,
            NotificationHistory.price_status == status,
            NotificationHistory.timeframe == timeframe
        ).order_by(NotificationHistory.timestamp.desc()).first()

        if last_notification:
            return (current_time - last_notification.timestamp) > user.notification_timeout
        return True

    def update_notification_history(self, session, user, symbol, notification_type, status, timeframe, timestamp):
        new_notification = NotificationHistory(
            user_id=user.id,
            symbol=symbol,
            notification_type=notification_type,
            price_status=status,
            timeframe=timeframe,
            timestamp=timestamp
        )
        session.add(new_notification)

    async def send_price_notification(self, context, user, symbol, status, timeframe):
        message = self.create_price_notification_message(symbol, status, timeframe)
        chart = self.create_chart(symbol, timeframe)
        await context.bot.send_photo(user.id, photo=chart, caption=message)

    def create_price_notification_message(self, symbol, status, timeframe):
        timeframe_str = "краткосрочном" if timeframe == '15m' else "долгосрочном"
        status_str = "верхнем" if status == 'high' else "нижнем"
        return f"Уведомление о цене для {symbol}: цена в {status_str} диапазоне на {timeframe_str} графике ({timeframe})"

    # ... (implement similar methods for FVG and OI notifications)

    def check_price_status(self, market):
        # Implement price status check
        pass

    def check_fvg_status(self, market):
        # Implement FVG status check
        pass

    def check_oi_status(self, market):
        # Implement Open Interest status check
        pass

    def create_notification_message(self, symbol, status_15m, status_4h):
        current_price = self.exchange.get_mark_price(symbol)
        market = self.exchange.get_market(symbol)
        
        if current_price is not None:
            message = f"Уведомление для {symbol} (текущая цена: {current_price:.2f} USDT):\n"
        else:
            message = f"Уведомление для {symbol}:\n"
            self.logger.warning(f"Unable to fetch mark price for {symbol}")
        
        if status_15m != 'normal':
            range_type = 'верхнем' if status_15m == 'high' else 'нижнем'
            time_range = market.get_chart_time_range('15m')
            message += f"Краткосрочный график ({time_range}): цена в {range_type} диапазоне\n"
        
        if status_4h != 'normal':
            range_type = 'верхнем' if status_4h == 'high' else 'нижнем'
            time_range = market.get_chart_time_range('4h')
            message += f"Долгосрочный график ({time_range}): цена в {range_type} диапазоне\n"
        
        return message

    def create_chart(self, symbol: str, timeframe: str):
        market = self.exchange.get_market(symbol)
        if market is None:
            self.logger.error(f"Market not found for symbol: {symbol}")
            return None

        candles = market.get_candles(timeframe)
        if candles is None or candles.empty:
            self.logger.error(f"No candle data for {symbol} on {timeframe} timeframe")
            return None

        time_range = market.get_chart_time_range(timeframe)
        try:
            return self.chart_generator.generate_candlestick_chart(candles, symbol, timeframe, time_range)
        except Exception as e:
            self.logger.exception(f"Error generating chart for {symbol}")
            return None
