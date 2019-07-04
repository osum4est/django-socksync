import time
from abc import ABC, abstractmethod
from threading import Lock
from typing import Set, cast, TypeVar, Generic, Callable, Dict, Optional
from uuid import uuid4

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
    def _handle_func(self, func: str, data: dict = None, socket: _SockSyncSocket = None) -> Optional[dict]:
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

    def _handle_func(self, func: str, data: dict = None, socket: _SockSyncSocket = None) -> Optional[dict]:
        # TODO: This is going through if socket is not subscribed
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
    _returns: Dict[str, dict] = {}
    _ignore_returns: Set[str] = set()
    _functions: Dict[Callable, 'SockSyncFunction'] = {}

    def __init__(self, name: str, function: Callable):
        super().__init__(name, "function")
        self.function = function
        self._functions[function] = self

    @staticmethod
    def function(remote: bool):
        def decorator(func: Callable):
            def wrapper(**kwargs):
                if remote:
                    ss_func = SockSyncFunction._functions[wrapper]
                    socket: _SockSyncConsumer = kwargs.get("socket", None)

                    id_ = str(uuid4())
                    json = dict(
                        **ss_func._to_json(),
                        func="call",
                        id=id_,
                        args=kwargs)

                    # Just call the function on each client and ignore returns
                    if socket is None:
                        for socket in ss_func._subscriber_sockets:
                            SockSyncFunction._ignore_returns.add(id_)
                            socket.send_json(json)
                            id_ = str(uuid4())
                            json["id"] = id_
                        return

                    # Call the function on the socket and wait for a response
                    socket.send_json(json)
                    while id_ not in SockSyncFunction._returns:
                        time.sleep(.25)

                    return_data = SockSyncFunction._returns[id_]
                    SockSyncFunction._returns.pop(id_)

                    return return_data
                else:
                    return func(**kwargs)

            return wrapper

        return decorator

    def _handle_func(self, func: str, data: dict = None, socket: _SockSyncSocket = None) -> Optional[dict]:
        if "id" not in data and socket is not None:
            socket.send_general_error("id is required.")
            return None

        id_ = data["id"]

        if func == "call" and socket.subscribed(self):
            return dict(**self._to_json(), func="return", id=id_, value=self.function(**data.get("args", {})))
        elif func == "return":
            if id_ in self._ignore_returns:
                self._ignore_returns.remove(id_)
            else:
                self._returns[id_] = data.get("value", None)
