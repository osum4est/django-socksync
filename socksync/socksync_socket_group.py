class SockSyncSocketGroup:
    _sockets = set()

    def __init__(self, name, type):
        self._name = name
        self._type = type

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    def add_socket(self, socket):
        self._sockets.add(socket)

    def remove_socket(self, socket):
        self._sockets.remove(socket)

    def send_update(self):
        for socket in self._sockets:
            socket.send_update(self)

    def to_json(self, op):
        return {
            "type": self.type,
            "op": op,
            "name": self.name,
        }
