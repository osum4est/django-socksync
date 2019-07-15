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

        self._variables: Dict[str, _LocalVariable] = {}
        self._lists: Dict[str, _LocalList] = {}
        self._functions: Dict[str, _LocalFunction] = {}

    def register_variable(self, var: _LocalVariable):
        self._variables[var.name] = var

    def register_list(self, var: _LocalList):
        self._lists[var.name] = var

    def register_function(self, function: _LocalFunction):
        self._functions[function.name] = function

    def connect(self):
        self.accept()
        if hasattr(socksync, "on_new_connection") and socksync.on_new_connection is not None:
            socksync.on_new_connection(self)

    def disconnect(self, _):
        self._remove_all_subscribers()
        self._variables.clear()
        self._lists.clear()
        self._functions.clear()

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

        if type_ == "var":
            self._handle_func(func, self._variables, name, request)
        elif type_ == "list":
            self._handle_func(func, self._lists, name, request)
        elif type_ == "function":
            self._handle_func(func, self._functions, name, request)
        else:
            self._send_error(SockSyncErrors.ERROR_INVALID_TYPE, f"{type_} is not a valid type.")

    def _handle_func(self, func: str, socket_groups: Dict[str, _Group], name: str, data: map):
        if name in socket_groups:
            socket_groups[name]._handle_func(func, data, self)
        else:
            self._send_error(SockSyncErrors.ERROR_INVALID_NAME, f"{name} is not registered.")

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
