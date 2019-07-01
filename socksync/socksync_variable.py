from threading import Lock

from socksync.socksync_socket_group import SockSyncSocketGroup


class SockSyncVariable(SockSyncSocketGroup):
    def __init__(self, name, value=None):
        super().__init__(name, "var")
        self._value = value
        self._lock = Lock()

    @property
    def value(self):
        with self._lock:
            return self._value

    @value.setter
    def value(self, new_value):
        with self._lock:
            self._value = new_value
        data = self.handle_func("get")
        self.send_json_to_all(data)

    def handle_func(self, func, data=None) -> dict:
        with self._lock:
            if func == "get":
                return dict(func="update", value=self._value, **self.to_json())
            elif func == "update" and "value" in data:
                self._value = data["value"]
