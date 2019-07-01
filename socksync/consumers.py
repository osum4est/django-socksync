import json
from json import JSONDecodeError

from channels.generic.websocket import WebsocketConsumer

from socksync import registry
from socksync.utils import dict_without_none


class SockSyncConsumer(WebsocketConsumer):
    _socket_groups = set()

    def connect(self):
        self.accept()

    def disconnect(self, code):
        for group in self._socket_groups:
            group.remove_socket(self)

    def receive(self, text_data=None, byte_data=None):
        try:
            request = json.loads(text_data)
        except JSONDecodeError:
            self.send_general_error("Invalid json.")
            return

        self.do_request(request)

    def do_request(self, request):
        if "func" not in request:
            self.send_general_error("func is required.")
            return
        else:
            func = request["func"]

        if func == "error":
            return

        if func == "unsubscribe_all":
            # TODO
            return

        if "type" not in request:
            self.send_general_error("type is required.")
            return
        else:
            type_ = request["type"]

        if "name" not in request:
            self.send_general_error("name is required.")
            return
        else:
            name = request["name"]

        if type_ == "var" and name in registry.variables:
            self.handle_func(func, type_, registry.variables, name, request)
        elif type_ == "list":
            self.handle_func(func, type_, registry.lists, name, request)
        elif type_ == "function":
            self.handle_func(func, type_, registry.functions, name, request)
        else:
            self.send_general_error("Unsupported type.")

    def handle_func(self, func, type_, socket_groups, name, data):
        if name in socket_groups:
            socket_group = socket_groups[name]

            if func == "subscribe":
                self._socket_groups.add(socket_group)
                socket_group.add_socket(self)
                return
            elif func == "unsubscribe":
                self._socket_groups.remove(socket_group)
                socket_group.remove_socket(self)
                return

            data = socket_group.handle_func(func, data)
            if data is not None:
                self.send_json(data)
        else:
            self.send_name_error(type_, name)

    def send_name_error(self, type_, name, id_=None):
        self.send_json({
            "func": "error",
            "type": type_,
            "name": name,
            "id": id_
        }, True)

    def send_general_error(self, message):
        self.send_json({
            "func": "error",
            "message": message
        })

    def send_json(self, data, strip_none=False):
        if strip_none:
            data = dict_without_none(data)
        self.send(json.dumps(data))
