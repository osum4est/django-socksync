from abc import ABC, abstractmethod
from threading import Lock
from typing import Set, cast, TypeVar, Generic, Callable

from django.db.models.signals import post_save

_SockSyncSocket = 'SockSyncSocket'
_SockSyncConsumer = 'SockSyncConsumer'


class SockSyncGroup(ABC):
    def __init__(self, name: str, type_: str):
        self._name: str = name
        self._type: str = type_

        self._subscriber_sockets: Set[_SockSyncSocket] = set()

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> str:
        return self._type

    @abstractmethod
    def _handle_func(self, func: str, data: dict = None, socket: _SockSyncSocket = None) -> dict:
        pass

    def _add_subscriber_socket(self, socket: _SockSyncSocket):
        self._subscriber_sockets.add(socket)

    def _remove_subscriber_socket(self, socket: _SockSyncSocket):
        self._subscriber_sockets.remove(socket)

    def _send_json_to_all(self, data: dict):
        for socket in self._subscriber_sockets:
            cast(_SockSyncConsumer, socket).send_json(data)

    def _send_json_to_others(self, data: dict, self_socket: _SockSyncSocket):
        for socket in self._subscriber_sockets:
            if socket != self_socket:
                cast(_SockSyncConsumer, socket).send_json(data)

    def _to_json(self) -> dict:
        return {
            "type": self._type,
            "name": self.name
        }


T = TypeVar('T')


class SockSyncVariable(SockSyncGroup, Generic[T]):
    def __init__(self, name: str, value: T = None):
        super().__init__(name, "var")
        self._value: T = value
        self._lock: Lock = Lock()

    @property
    def value(self) -> T:
        with self._lock:
            return self._value

    @value.setter
    def value(self, new_value: T):
        with self._lock:
            self._value = new_value
        self._send_json_to_all(self._handle_func("get"))

    def _handle_func(self, func: str, data: dict = None, socket: _SockSyncSocket = None) -> dict:
        if func == "get" and (socket is None or socket.subscribed(self)):
            return dict(func="set", value=self.value, **self._to_json())
        elif func == "set" and "value" in data and socket.subscribed(self):
            with self._lock:
                self._value = data["value"]
            self._send_json_to_others(self._handle_func("get"), socket)


class SockSyncList(SockSyncGroup):
    value = []

    def get(self, index: int) -> object:
        return self.value[index]

    def set(self, index: int, value: object):
        self.value[index] = value
        # TODO: Update subscribers


class SockSyncModelList(SockSyncList):
    def __init__(self, model):
        self.model = model
        post_save.connect(self._model_post_save, sender=model)

    def get(self, index: int) -> object:
        pass

    def set(self, index: int, value: object):
        pass

    def _model_post_save(self):
        pass


class SockSyncFunction(SockSyncGroup):
    @stat
    _calls = {}

    def __init__(self, name: str, type_: str, function: Callable[[any], None]):
        super().__init__(name, type_)
        self.function = function

    @staticmethod
    def socksync_function(self, ):

    def _handle_func(self, func: str, data: dict = None, socket: _SockSyncSocket = None) -> dict:
        if func == "call" and socket.subscribed(self):
            return dict(func="return", value=self.function(**data["args"]), id=data["id"], **self._to_json())
        elif func == "return":
            # TODO

    async def hi(self):
