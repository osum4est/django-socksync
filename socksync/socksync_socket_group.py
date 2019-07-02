from abc import ABC, abstractmethod
from typing import Set

from socksync.consumers import SockSyncConsumer


class SockSyncSocketGroup(ABC):
    _sockets: Set[SockSyncConsumer] = set()

    def __init__(self, name: str, type_: str):
        self._name: str = name
        self._type: str = type_

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> str:
        return self._type

    @abstractmethod
    def handle_func(self, func: str, data: dict = None) -> dict:
        pass

    def add_socket(self, socket: SockSyncConsumer):
        self._sockets.add(socket)

    def remove_socket(self, socket: SockSyncConsumer):
        self._sockets.remove(socket)

    def send_json_to_all(self, data: dict):
        for socket in self._sockets:
            socket.send_json(data)

    def to_json(self) -> dict:
        return {
            "type": self._type,
            "name": self.name
        }
