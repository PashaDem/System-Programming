from __future__ import annotations
import socket
from enum import StrEnum, auto
from typing import Tuple
from uuid import UUID, uuid4

import chat


class User:
    chat: 'chat.Chat' = None
    addr: Tuple[str, int] = None
    status: 'Status'
    conn: socket.socket = None

    def __init__(self, addr, conn):
        self.user_id: UUID = uuid4()
        self.status = Status.OUT_OF_CHAT
        self.addr = addr
        self.conn = conn

    def send_message(self, message: bytes):
        if self.status == Status.IN_CHAT and self.chat:
            self.chat.publish_message(message, except_list=[self])


class Status(StrEnum):
    IN_CHAT = auto()
    OUT_OF_CHAT = auto()
