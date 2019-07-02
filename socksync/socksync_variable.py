from threading import Lock
from typing import TypeVar, Generic

from socksync.socksync_socket_group import SockSyncSocketGroup

T = TypeVar('T')


class SockSyncVariable(SockSyncSocketGroup, Generic[T]):
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
        self.send_json_to_all(self.handle_func("get"))

    def handle_func(self, func: str, data: dict = None) -> dict:
        with self._lock:
            if func == "get":
                return dict(func="update", value=self._value, **self.to_json())
            elif func == "update" and "value" in data:
                self._value = data["value"]
