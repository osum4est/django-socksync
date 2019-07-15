from typing import Callable, Set

from socksync.sockets import SockSyncSocket

NewConnectionHandler = Callable[[SockSyncSocket], None]
_new_connection_handlers: Set[NewConnectionHandler] = set()


def add_new_connection_handler(on_new_connection: NewConnectionHandler):
    global _new_connection_handlers
    _new_connection_handlers.add(on_new_connection)


def remove_new_connection_handler(on_new_connection: NewConnectionHandler):
    global _new_connection_handlers
    if on_new_connection in _new_connection_handlers:
        _new_connection_handlers.remove(on_new_connection)

# TODO: filtering
# TODO: Unit testing
