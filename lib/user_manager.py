import logging
import time
from telegram import Update, Chat
from lib.models import User, ChatGroup


class UserManager:
    def __init__(self, session_maker):
        self.Session = session_maker
        self.logger = logging.getLogger(__name__)

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
