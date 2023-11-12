import os
import socket
import selectors
import types
from typing import Dict, List, Tuple, Literal
from uuid import uuid4, UUID


class User:
    chat: 'Chat' = None
    addr: Tuple[str, int] = None
    status: Literal['in_chat', 'out_of_chat']
    conn: socket.socket = None

    def __init__(self, addr, conn):
        self.user_id: UUID = uuid4()
        self.status = 'out_of_chat'
        self.addr = addr
        self.conn = conn

    def send_message(self, message: bytes):
        if self.status == 'in_chat' and self.chat:
            self.chat.publish_message(message)


class Chat:
    def __init__(self):
        self.chat_id = uuid4()
        self.users: List['User'] = []

    def delete_user(self, user_id: UUID):
        for i, user in enumerate(self.users):
            if user.user_id == user_id:
                del self.users[i]
                break

    def publish_message(self, message: bytes):
        for user in self.users:
            user.conn.send(message)


class ConnectionServer:

    def __init__(self, host: str = '127.0.0.1', port: int = 8000):
        self.users: List['User'] = []
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
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.selector.register(conn, events, data=data)
        conn.send(b'Enter the identifier of the session:')
        self.users.append(User(addr=addr, conn=conn))

    def remove_connection_wrapper(self, data, sock):
        for i, user in enumerate(self.users):
            if data.addr == user.addr:
                if user.chat:
                    user.chat.delete_user(user.user_id)
                del self.users[i]
                break
        print(f"Closing connection to {data.addr}")
        self.selector.unregister(sock)
        sock.close()

    def service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                data.outb += recv_data
            else:
                # need to delete the user from the chat and from the ConnectionServer's collection
                self.remove_connection_wrapper(data=data, sock=sock)
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                print(f"Echoing {data.outb!r} to {data.addr}")
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]


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
