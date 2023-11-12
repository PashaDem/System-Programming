import os
import socket
import selectors
import types
from typing import Dict, List, Tuple, Union
from uuid import uuid4, UUID
from enum import StrEnum, auto
import logging


class Status(StrEnum):
    IN_CHAT = auto()
    OUT_OF_CHAT = auto()


class User:
    chat: 'Chat' = None
    addr: Tuple[str, int] = None
    status: Status
    conn: socket.socket = None

    def __init__(self, addr, conn):
        self.user_id: UUID = uuid4()
        self.status = Status.OUT_OF_CHAT
        self.addr = addr
        self.conn = conn

    def send_message(self, message: bytes):
        if self.status == Status.IN_CHAT and self.chat:
            self.chat.publish_message(message, except_list=[self])


class Chat:
    def __init__(self):
        self.chat_id = uuid4()
        self.users: List['User'] = []

    def delete_user(self, user_id: UUID):
        for i, user in enumerate(self.users):
            if user.user_id == user_id:
                del self.users[i]
                user.status = Status.OUT_OF_CHAT
                user.chat = None
                break

    def add_user(self, user: 'User'):
        self.users.append(user)
        user.chat = self
        user.status = Status.IN_CHAT

    def publish_message(self, message: bytes, except_list: List['User']):
        for user in self.users:
            if user not in except_list:
                user.conn.send(message)


class ConnectionServer:

    def __init__(self, host: str = '127.0.0.1', port: int = 8000):
        self.users: List['User'] = []
        self.chats: List['Chat'] = []
        self.session_collection: Dict[UUID, List[socket.socket]] = {}
        self.selector = selectors.DefaultSelector()
        self.listener_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener_sock.bind((host, port))
        self.listener_sock.setblocking(False)
        self.listener_sock.listen()
        self.selector.register(self.listener_sock, selectors.EVENT_READ, data=None)

    def run(self):
        try:
            while True:
                events = self.selector.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_connection_wrapper(key.fileobj)
                    else:
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            print('Caught keyboard interrupt, exiting')
        finally:
            self.selector.close()

    def accept_connection_wrapper(self, sock: socket.socket):
        conn, addr = sock.accept()
        print(f'Accepted connection from {addr}')
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
        events = selectors.EVENT_READ #| selectors.EVENT_WRITE
        self.selector.register(conn, events, data=data)
        conn.send(b'Enter the command:\n')
        self.users.append(User(addr=addr, conn=conn))

    def remove_connection_wrapper(self, data, sock):
        for i, user in enumerate(self.users):
            if data.addr == user.addr:
                if user.chat:
                    self.delete_user_from_chat(user)
                del self.users[i]
                break
        print(f"Closing connection to {data.addr}")
        self.selector.unregister(sock)
        sock.close()

    def delete_user_from_chat(self, user: 'User'):
        user.send_message(bytes(f'The user {user.user_id} left the chat.\n'.encode()))
        user.chat.delete_user(user.user_id)

    def add_user_to_chat(self, user: 'User', chat: 'Chat'):
        chat.add_user(user)
        chat.publish_message(bytes(f'User {user.user_id} has been added to the chat.\n'.encode()), except_list=[])

    def create_chat(self, user: 'User'):
        chat = Chat()
        print('Chat was created')
        chat.add_user(user)
        print('User was added to the chat')
        self.chats.append(chat)
        print('Added chat to ConnServ chat list')
        user.conn.send(bytes(f'Chat was created with identifier: `{chat.chat_id}`\n'.encode()))
        print('Sent message')

    def get_user_by_address(self, addr) -> Union[None, 'User']:
        user_list = [user for user in filter(lambda user: user.addr == addr, self.users)]
        print(f'user list {user_list}')
        return user_list[0] if len(user_list) else None

    def service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                buff: bytes = recv_data
                user = self.get_user_by_address(data.addr)
                decoded_command = buff.decode().rstrip()
                if user.status == Status.IN_CHAT:
                    print('In chat processing')
                    if decoded_command == ':exit' or decoded_command == ':quit':
                        print('deleting user from the chat')
                        self.delete_user_from_chat(user)
                        print('user deleted from the chat')
                    else:
                        print('user publishing message')
                        user.send_message(buff)

                else:  # not in chat now
                    print('Out of chat proceessing')
                    if decoded_command == ':exit' or decoded_command == ':quit':
                        print('inside exit statement')
                        self.remove_connection_wrapper(data=data, sock=sock)
                    elif decoded_command == ':create':
                        print('Creating the chat')
                        self.create_chat(user)

                    else:
                        print('UUID parsing')
                        is_uuid = False
                        try:
                            print('before uuiding')
                            identifier = UUID(decoded_command[1:])
                            print('after uuiding')
                        except ValueError as e:
                            print('Not uuid')
                            logging.exception(e)
                            user.conn.send(b'Unknown command.\n')
                        else:

                            # decoded command contains the uuid of potential chat
                            print(f'Connecting to service with uuid {identifier}')
                            potential_chat_identifier = identifier
                            print(f'Identifier {identifier}')
                            chat_rooms = [chat for chat in filter(lambda chat_room: chat_room.chat_id == potential_chat_identifier, self.chats)]
                            chat_room = chat_rooms[0] if len(chat_rooms) else None
                            if chat_rooms is None:
                                print('No chat with such uuid')
                                user.conn.send(bytes(f'There is no chat room with id = `{potential_chat_identifier}`'.encode()))
                            else:
                                print('adding user to the chat')
                                self.add_user_to_chat(user, chat_room)


if __name__ == '__main__':
    host = os.environ.get('HOST')
    port = os.environ.get('PORT')
    # if host and port:
    #     chat = Chat(host=host, port=port)
    # else:
    chat = ConnectionServer()
    try:
        chat.run()
    except Exception:
        pass
    finally:
        chat.selector.close()

# !/usr/bin/env python3

# import sys
# import socket
# import selectors
# import types
#
# sel = selectors.DefaultSelector()
#
#
# def accept_wrapper(sock):
#     conn, addr = sock.accept()  # Should be ready to read
#     print(f"Accepted connection from {addr}")
#     conn.setblocking(False)
#     data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
#     events = selectors.EVENT_READ | selectors.EVENT_WRITE
#     sel.register(conn, events, data=data)
#
#
# def service_connection(key, mask):
#     sock = key.fileobj
#     data = key.data
#     if mask & selectors.EVENT_READ:
#         recv_data = sock.recv(1024)  # Should be ready to read
#         if recv_data:
#             data.outb += recv_data
#         else:
#             print(f"Closing connection to {data.addr}")
#             sel.unregister(sock)
#             sock.close()
#     if mask & selectors.EVENT_WRITE:
#         if data.outb:
#             print(f"Echoing {data.outb!r} to {data.addr}")
#             sent = sock.send(data.outb)  # Should be ready to write
#             data.outb = data.outb[sent:]
#
#
# if len(sys.argv) != 3:
#     print(f"Usage: {sys.argv[0]} <host> <port>")
#     sys.exit(1)
#
# host, port = sys.argv[1], int(sys.argv[2])
# lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# lsock.bind((host, port))
# lsock.listen()
# print(f"Listening on {(host, port)}")
# lsock.setblocking(False)
# sel.register(lsock, selectors.EVENT_READ, data=None)
#
# try:
#     while True:
#         events = sel.select(timeout=None)
#         for key, mask in events:
#             if key.data is None:
#                 accept_wrapper(key.fileobj)
#             else:
#                 service_connection(key, mask)
# except KeyboardInterrupt:
#     print("Caught keyboard interrupt, exiting")
# finally:
#     sel.close()
