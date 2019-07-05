import json
from abc import ABC, abstractmethod
from json import JSONDecodeError
from typing import Set, Dict

from channels.generic.websocket import WebsocketConsumer

from socksync import socksync
from socksync.utils import dict_without_none

_SockSyncGroup = 'SockSyncGroup'
_SockSyncVariable = 'SockSyncVariable'
_SockSyncFunction = 'SockSyncFunction'

class SockSyncSocket(ABC):
    @abstractmethod
    def register_variable(self, var: _SockSyncVariable):
        pass
    
    @abstractmethod
    def register_function(self, var: _SockSyncFunction):
        pass

    @abstractmethod
    def subscribed(self, group: _SockSyncGroup) -> bool:
        pass

    @abstractmethod
    def subscribe(self, group: _SockSyncGroup):
        pass

    @abstractmethod
    def unsubscribe(self, group: _SockSyncGroup):
        pass

    @abstractmethod
    def unsubscribe_all(self):
        pass


# noinspection PyProtectedMember
class SockSyncConsumer(WebsocketConsumer, SockSyncSocket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._subscriber_groups: Set[_SockSyncGroup] = set()
        self._subscription_groups: Set[_SockSyncGroup] = set()

        self._variables: Dict[str, _SockSyncGroup] = {}
        self._lists: Dict[str, _SockSyncGroup] = {}
        self._functions: Dict[str, _SockSyncGroup] = {}

    def register_variable(self, var: _SockSyncVariable):
        self._variables[var.name] = var

    def register_function(self, function: _SockSyncFunction):
        self._functions[function.name] = function

    def connect(self):
        self.accept()
        if hasattr(socksync, "on_new_connection") and socksync.on_new_connection is not None:
            socksync.on_new_connection(self)

    def disconnect(self, _):
        self.remove_all_subscribers()
        self._variables.clear()
        self._lists.clear()
        self._functions.clear()

    def receive(self, text_data: dict = None, _=None):
        try:
            request = json.loads(text_data)
        except JSONDecodeError:
            self.send_general_error("Invalid json.")
            return

        self.do_request(request)

    def do_request(self, request: dict):
        if "func" not in request:
            self.send_general_error("func is required.")
            return
        else:
            func = request["func"]

        if func == "error":
            return

        if func == "unsubscribe_all":
            self.remove_all_subscribers()
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

        if type_ == "var":
            self.handle_func(func, type_, self._variables, name, request)
        elif type_ == "list":
            self.handle_func(func, type_, self._lists, name, request)
        elif type_ == "function":
            self.handle_func(func, type_, self._functions, name, request)
        else:
            self.send_general_error("Unsupported type.")

    def handle_func(self, func: str, type_: str, socket_groups: Dict[str, _SockSyncGroup], name: str, data: map):
        if name in socket_groups:
            socket_group = socket_groups[name]

            if func == "subscribe":
                self._subscriber_groups.add(socket_group)
                socket_group._add_subscriber_socket(self)
                return
            elif func == "unsubscribe":
                self._subscriber_groups.remove(socket_group)
                socket_group._remove_subscriber_socket(self)
                return

            data = socket_group._handle_func(func, data, self)
            if data is not None:
                self.send_json(data)
        else:
            self.send_name_error(type_, name)

    def subscribed(self, group: _SockSyncGroup) -> bool:
        return group in self._subscription_groups

    def subscribe(self, group: _SockSyncGroup):
        if not group._subscribable:
            raise Exception("Group is not subscribable!")

        self.send_json(dict(func="subscribe", **group._to_json()))
        self._subscription_groups.add(group)

    def unsubscribe(self, group: _SockSyncGroup):
        if not group._subscribable:
            raise Exception("Group is not subscribable!")

        self.send_json(dict(func="unsubscribe", **group._to_json()))
        self._subscription_groups.remove(group)

    def unsubscribe_all(self):
        self.send_json(dict(func="unsubscribe_all"))
        self._subscription_groups.clear()

    def remove_all_subscribers(self):
        for group in self._subscriber_groups:
            group._remove_subscriber_socket(self)
        self._subscriber_groups.clear()

    def send_name_error(self, type_: str, name: str, id_: str = None):
        self.send_json({
            "func": "error",
            "type": type_,
            "name": name,
            "id": id_
        }, True)

    def send_general_error(self, message: str):
        self.send_json({
            "func": "error",
            "message": message
        })

    def send_json(self, data: dict, strip_none: bool = False):
        if strip_none:
            data = dict_without_none(data)
        self.send(json.dumps(data))
