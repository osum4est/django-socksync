import json
from json import JSONDecodeError
from typing import Set, Dict

from channels.generic.websocket import WebsocketConsumer

from socksync import socksync
from socksync.errors import SockSyncErrors

_Group = 'Group'
_LocalGroup = 'LocalGroup'
_RemoteGroup = 'RemoteGroup'
_LocalVariable = 'LocalVariable'
_LocalList = 'LocalList'
_LocalFunction = 'LocalFunction'


class SockSyncSocket(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._subscriber_groups: Set[_LocalGroup] = set()
        self._subscription_groups: Set[_RemoteGroup] = set()

        self._registry: Dict[str, Dict[str, _LocalGroup]] = {"var": {}, "list": {}, "function": {}}

    def register_group(self, var: _LocalGroup):
        self._registry[var.type][var.name] = var

    def connect(self):
        self.accept()
        for handler in socksync._new_connection_handlers:
            handler(self)

    def disconnect(self, _):
        self._remove_all_subscribers()
        for r in self._registry.values():
            r.clear()

    def receive(self, text_data: str = None, _=None):
        try:
            request = json.loads(text_data)
        except JSONDecodeError:
            self._send_error(SockSyncErrors.ERROR_INVALID_JSON, "Invalid json.")
            return

        self._do_request(request)

    def _do_request(self, request: dict):
        if "func" not in request:
            self._send_error(SockSyncErrors.ERROR_INVALID_FUNC, "func is required.")
            return
        else:
            func = request["func"]

        if func == "error":
            return

        if func == "unsubscribe_all":
            self._remove_all_subscribers()
            return

        if "type" not in request:
            self._send_error(SockSyncErrors.ERROR_INVALID_TYPE, "type is required.")
            return
        else:
            type_ = request["type"]

        if "name" not in request:
            self._send_error(SockSyncErrors.ERROR_INVALID_NAME, "name is required.")
            return
        else:
            name = request["name"]

        if type_ in self._registry:
            if name in self._registry[type_]:
                self._registry[type_][name]._handle_func(func, request, self)
            else:
                self._send_error(SockSyncErrors.ERROR_INVALID_NAME, f"{name} is not registered.")
        else:
            self._send_error(SockSyncErrors.ERROR_INVALID_TYPE, f"{type_} is not a valid type.")

    def unsubscribe_all(self):
        self._send_json({'func': "unsubscribe_all"})
        for group in self._subscription_groups:
            group._subscribed = False

        self._subscription_groups.clear()

    def _remove_all_subscribers(self):
        for group in self._subscriber_groups:
            group._socket_unsubscribed(self)
        self._subscriber_groups.clear()

    def _add_subscriber(self, group: _LocalGroup):
        self._subscriber_groups.add(group)

    def _remove_subscriber(self, group: _LocalGroup):
        self._subscriber_groups.remove(group)

    def _add_subscription(self, group: _RemoteGroup):
        self._subscription_groups.add(group)

    def _remove_subscription(self, group: _RemoteGroup):
        self._subscription_groups.remove(group)

    def _send_error(self, error_code: int, message: str):
        self._send_json({
            "func": "error",
            "error_code": error_code,
            "message": message
        })

    def _send_json(self, data: dict):
        self.send(json.dumps(data))
