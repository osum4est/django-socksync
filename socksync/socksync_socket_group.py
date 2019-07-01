from abc import ABC, abstractmethod


class SockSyncSocketGroup(ABC):
    _sockets = set()

    def __init__(self, name, type_):
        self._name = name
        self._type = type_

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @abstractmethod
    def handle_func(self, func, data=None) -> dict:
        pass

    def add_socket(self, socket):
        self._sockets.add(socket)

    def remove_socket(self, socket):
        self._sockets.remove(socket)

    def send_json_to_all(self, data):
        for socket in self._sockets:
            socket.send_json(data)

    def to_json(self):
        return {
            "type": self._type,
            "name": self.name
        }
