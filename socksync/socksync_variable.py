from socksync.socksync_socket_group import SockSyncSocketGroup


class SockSyncVariable(SockSyncSocketGroup):
    def __init__(self, name, value=None):
        super().__init__(name, "var")
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        self.send_update()

    def to_json(self, op):
        json = super().to_json(op)

        if op == "update":
            json["value"] = self.value

        return json
