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

    def receive(self, text_data=None, bytes_data=None):
        try:
            request = json.loads(text_data)
        except JSONDecodeError:
            self.send_general_error("Invalid json.")
            return

        self.do_request(request)
        # async_to_sync(self.channel_layer.group_send)(
        #     get_group_name(request),
        #     {
        #         'type': 'test',
        #         'hi': socksync.__get("hi")
        #     }
        # )

    def do_request(self, request):
        if "type" not in request:
            self.send_general_error("Type is required.")
            return
        else:
            type = request["type"]

        if type == "error":
            return

        if type == "unsubscribe_all":
            # TODO
            return

        if "name" not in request:
            self.send_general_error("Name is required.")
            return
        else:
            name = request["name"]

        if "op" not in request:
            self.send_general_error("Operation is required.")
            return
        else:
            op = request["op"]

        id = None
        if "id" in request:
            id = request["id"]

        if op == "error":
            return

        if op == "subscribe":
            # TODO
            return

        if op == "unsubscribe":
            # TODO
            return

        if type == "var":
            if op == "get":
                if name in registry.variables:
                    self.send_update(registry.variables[name])
                    self._socket_groups.add(registry.variables[name])
                    registry.variables[name].add_socket(self)
                else:
                    self.send_type_error("var", name)
            else:
                self.send_general_error("Unsupported operation for var.")
        else:
            self.send_general_error("Unsupported type.")

    def send_update(self, socket_group):
        self.send(json.dumps(socket_group.to_json("update")))

    def send_type_error(self, type, name, id=None):
        self.send(json.dumps(dict_without_none({
            "type": type,
            "op": "error",
            "name": name,
            "id": id
        })))

    def send_general_error(self, message):
        self.send(json.dumps({
            "type": "error",
            "message": message
        }))
