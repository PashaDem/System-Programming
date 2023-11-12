import logging
import selectors
import socket
import types
from typing import List, Dict, Union
from uuid import UUID

from chat.chat import Chat
from chat.user import User, Status


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
        chat.add_user(user)
        self.chats.append(chat)
        user.conn.send(bytes(f'Chat was created with identifier: `{chat.chat_id}`\n'.encode()))

    def get_user_by_address(self, addr) -> Union[None, 'User']:
        user_list = [user for user in filter(lambda user: user.addr == addr, self.users)]
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
                    if decoded_command == ':exit' or decoded_command == ':quit':
                        self.delete_user_from_chat(user)
                    else:
                        user.send_message(buff)

                else:  # not in chat now
                    if decoded_command == ':exit' or decoded_command == ':quit':
                        self.remove_connection_wrapper(data=data, sock=sock)
                    elif decoded_command == ':create':
                        self.create_chat(user)

                    else:
                        is_uuid = False
                        try:
                            identifier = UUID(decoded_command[1:])
                        except ValueError as e:
                            logging.exception(e)
                            user.conn.send(b'Unknown command.\n')
                        else:
                            # decoded command contains the uuid of potential chat
                            potential_chat_identifier = identifier
                            chat_rooms = [chat for chat in filter(lambda chat_room: chat_room.chat_id == potential_chat_identifier, self.chats)]
                            chat_room = chat_rooms[0] if len(chat_rooms) else None
                            if chat_rooms is None:
                                user.conn.send(bytes(f'There is no chat room with id = `{potential_chat_identifier}`'.encode()))
                            else:
                                self.add_user_to_chat(user, chat_room)
