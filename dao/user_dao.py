from model.entity.user import User
from model.entity.base import Session
import hashlib
from sqlalchemy import select


class UserDao:

    def __init__(self):
        self.session = Session

    def edit_user(self, user: User):
        self.session.add(user)
        self.session.commit()

    def get_user_by_chat_id(self, user_chat_id: int):
        bytes_string_chat_id = str(user_chat_id).encode()
        hashed_cid = hashlib.md5(bytes_string_chat_id).hexdigest()
        statement = select(User).where(User.hashed_chat_id == hashed_cid)
        result = self.session.execute(statement)
        users = result.scalars().all()
        if users:
            return users[0]
        else:
            # TODO: LOG NOTHING IS FOUND
            pass

    def add_user(self, user: User):
        if user:
            self.session.add(user)
            self.session.commit()
        else:
            # TODO: LOG
            pass

