from __future__ import annotations
from typing import List
from uuid import uuid4, UUID

import chat.user as usr


class Chat:
    def __init__(self):
        self.chat_id = uuid4()
        self.users: List['usr.User'] = []

    def delete_user(self, user_id: UUID):
        for i, user in enumerate(self.users):
            if user.user_id == user_id:
                del self.users[i]
                user.status = usr.Status.OUT_OF_CHAT
                user.chat = None
                break

    def add_user(self, user: 'usr.User'):
        self.users.append(user)
        user.chat = self
        user.status = usr.Status.IN_CHAT

    def publish_message(self, message: bytes, except_list: List['usr.User']):
        for user in self.users:
            if user not in except_list:
                user.conn.send(message)
