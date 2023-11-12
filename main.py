"""
Start point of the chat application.
"""

import logging

from chat.connection_server import ConnectionServer

if __name__ == '__main__':
    chat = ConnectionServer()
    try:
        chat.run()
    except Exception as e:
        logging.exception(e)
    finally:
        chat.selector.close()
