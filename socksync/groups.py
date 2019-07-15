import time
from abc import ABC, abstractmethod
from threading import Thread
from typing import Set, Callable, Dict, Optional, List, Tuple, Iterable
from uuid import uuid4

from django.core.paginator import Paginator

from socksync.errors import SockSyncErrors

_SockSyncSocket = 'SockSyncSocket'


class Group(ABC):
    ReceiveFunction = Callable[[dict, _SockSyncSocket], None]
    SendFunction = Callable[[dict, _SockSyncSocket], Optional[dict]]

    def __init__(self, name: str, type_: str):
        self._name: str = name
        self._type: str = type_
        self._receive_functions: Dict[str, Tuple[Group.ReceiveFunction, bool, List[str]]] = {}
        self._send_functions: Dict[str, Group.SendFunction] = {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> str:
        return self._type

    @abstractmethod
    def _get_sockets(self) -> List[_SockSyncSocket]:
        pass

    @abstractmethod
    def _is_subscribed(self, socket: _SockSyncSocket):
        pass

    def _handle_func(self, func: str, data: dict, socket: _SockSyncSocket):
        if func not in self._receive_functions:
            self._send_error(SockSyncErrors.ERROR_INVALID_FUNC, f"{func} is not valid for this group.", socket)
            return

        if self._receive_functions[func][1] and not self._is_subscribed(socket):
            self._send_error(SockSyncErrors.ERROR_INVALID_FUNC, f"Subscription required.", socket)
            return

        for required_field in self._receive_functions[func][2]:
            if required_field not in data:
                self._send_error(SockSyncErrors.ERROR_MISSING_FIELD, f"{required_field} is required.", socket)
                return

        try:
            self._receive_functions[func][0](data, socket)
        except Exception as e:
            self._send_error(SockSyncErrors.ERROR_OTHER, f"{e}", socket)

    def _register_receive(self, func: str, function: ReceiveFunction, require_subscription: bool,
                          required_fields: List[str] = None):
        self._receive_functions[func] = (function, require_subscription, required_fields or [])

    def _register_receive_send(self, func: str, response_func: str, require_subscription: bool,
                               required_fields: List[str] = None):
        self._register_receive(func, lambda data, socket: self._send_func(response_func, socket, args=data),
                               require_subscription, required_fields or [])

    def _register_send(self, func: str, function: SendFunction = None):
        self._send_functions[func] = function or (lambda: {})

    def _send_func(self, func: str, socket: _SockSyncSocket = None, args: dict = None):
        for s in [socket] if socket is not None else self._get_sockets():
            data = self._send_functions[func](args, s)
            if data is not None:
                s._send_json({'func': func, **self._to_json(), **data})

    def _send_json(self, data: dict, socket: _SockSyncSocket = None):
        for s in [socket] if socket is not None else self._get_sockets():
            s._send_json({**self._to_json(), **data})

    @staticmethod
    def _send_error(error_code: int, message: str, socket: _SockSyncSocket):
        socket._send_error(error_code, message)

    def _to_json(self) -> dict:
        return {
            "type": self._type,
            "name": self.name
        }


class RemoteGroup(Group, ABC):
    def __init__(self, name: str, type_: str, socket: _SockSyncSocket):
        super().__init__(name, type_)
        self._socket = socket
        self._subscribed = False

    def _get_sockets(self) -> List[_SockSyncSocket]:
        return [self._socket]

    def _is_subscribed(self, socket: _SockSyncSocket):
        return self._socket == socket and self.subscribed

    def subscribe(self):
        self._send_json({'func': "subscribe"})
        self._subscribed = True
        self._socket._add_subscription(self)

    def unsubscribe(self):
        self._send_json({'func': "unsubscribe"})
        self._subscribed = False
        self._socket._remove_subscription(self)

    @property
    def subscribed(self) -> bool:
        return self._subscribed


class LocalGroup(Group, ABC):
    def __init__(self, name: str, type_: str):
        super().__init__(name, type_)
        self._subscriber_sockets: Set[_SockSyncSocket] = set()

        self._register_receive("subscribe", self._socket_subscribed, False)
        self._register_receive("unsubscribe", self._socket_unsubscribed, True)

    def _socket_subscribed(self, _, socket: _SockSyncSocket):
        self._subscriber_sockets.add(socket)
        socket._add_subscriber(self)

    def _socket_unsubscribed(self, _, socket: _SockSyncSocket):
        self._subscriber_sockets.remove(socket)
        socket._remove_subscriber(self)

    def _get_sockets(self) -> List[_SockSyncSocket]:
        return [s for s in self._subscriber_sockets]

    def _is_subscribed(self, socket: _SockSyncSocket):
        return socket in self._subscriber_sockets


class RemoteVariable(RemoteGroup):
    def __init__(self, name: str, socket: _SockSyncSocket, subscribe: bool = True):
        super().__init__(name, "var", socket)
        socket._register_variable(self)
        self._value = None
        self._register_receive("set", self._recv_set, True, ["value"])
        self._register_send("get")

        if subscribe:
            self.subscribe()
            self.get()

    @property
    def value(self) -> any:
        return self._value

    def get(self):
        self._send_func("get")

    def _recv_set(self, data: dict, _):
        self._value = data["value"]


class LocalVariable(LocalGroup):
    def __init__(self, name: str, value: any = None):
        super().__init__(name, "var")
        self._value = value

        self._register_receive_send("get", "set", True)
        self._register_send("set", lambda: {'value': self._value})

    @property
    def value(self) -> any:
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self._send_func("set")


class RemoteList(RemoteGroup):
    def __init__(self, name: str, socket: _SockSyncSocket, page_size: int = 25, subscribe: bool = True):
        super().__init__(name, "list", socket)
        socket._register_list(self)
        self._items = []
        self._page = 0
        self._page_size = page_size
        self._total_item_count = 0

        self._register_receive("set_all", self._recv_set_all, True, ["page", "page_size", "total_item_count", "items"])
        self._register_receive("set_count", self._recv_set_count, True, ["total_item_count"])
        self._register_receive("set", self._recv_set, True, ["index", "value"])
        self._register_receive("insert", self._recv_insert, True, ["index", "value"])
        self._register_receive("delete", self._recv_delete, True, ["index"])

        self._register_send("get", lambda: {"page": self._page, "page_size": self._page_size})

        if subscribe:
            self.subscribe()
            self.get()

    @property
    def items(self) -> Iterable[any]:
        return (i for i in self._items)

    @property
    def page(self) -> int:
        return self._page

    @property
    def page_size(self) -> int:
        return self._page_size

    @property
    def count(self) -> int:
        return self._total_item_count

    def get(self):
        self._send_func("get")

    def _recv_set_all(self, data: dict, _):
        self._page = data["page"]
        self._page_size = data["page_size"]
        self._total_item_count = data["total_item_count"]
        self._items.clear()
        for item in data["items"]:
            self._items.append(item["value"])

    def _recv_set_count(self, data: dict, _):
        self._total_item_count = data["total_item_count"]

    def _recv_set(self, data: dict, socket: _SockSyncSocket):
        if data["index"] >= len(self._items):
            self._send_error(SockSyncErrors.ERROR_BAD_INDEX, f"{data['index']} is out of bounds.", socket)
            return

        self._items[data["index"]] = data["value"]

    def _recv_insert(self, data: dict, _):
        self._items.insert(data["index"], data["value"])
        self._total_item_count += 1

    def _recv_delete(self, data: dict, socket: _SockSyncSocket):
        if data["index"] >= len(self._items):
            self._send_error(SockSyncErrors.ERROR_BAD_INDEX, f"{data['index']} is out of bounds.", socket)
            return

        self._items.pop(data["index"])
        self._total_item_count -= 1


class LocalList(LocalGroup):
    def __init__(self, name: str, items: List[any] = None, max_page_size: int = 25):
        super().__init__(name, "list")
        self._items = []
        for item in items:
            self._items.append(item)

        self._max_page_size = max_page_size
        self._subscriber_pages: Dict[_SockSyncSocket, (int, int)] = {}

        self._register_receive_send("get", "set_all", True)

        self._register_send("set_all", self._send_set_all)
        self._register_send("set_count", lambda: {"total_item_count": len(self._items)})
        self._register_send("set", self._send_set)
        self._register_send("insert", self._send_insert)
        self._register_send("delete", self._send_delete)

    @property
    def items(self) -> Iterable[any]:
        return (i for i in self._items)

    def set(self, index, value):
        self._items[index] = value
        self._send_func("set", args={'index': index})

    def insert(self, index, value):
        # TODO: Send delete
        self._items.insert(index, value)
        self._send_func("insert", args={"index": index, "value": value})

    def append(self, value):
        self.insert(len(self._items) - 1, value)

    def delete(self, index):
        # TODO: Send insert
        self._items.pop(index)
        self._send_func("delete", args={"index": index})

    def _send_set_all(self, args: dict, _) -> Optional[dict]:
        page = args.get("page", 0)
        page_size = min(self._max_page_size, args.get("page_size", self._max_page_size))
        return {
            "page": page,
            "page_size": page_size,
            "total_item_count": len(self._items),
            "items": [v for v in Paginator(self._items, page_size).get_page(page)]
        }

    def _send_set(self, args: dict, socket: _SockSyncSocket) -> Optional[dict]:
        i = args["index"]
        socket_i = self._get_socket_index(i, socket)
        if socket_i is not None:
            return {
                "index": socket_i,
                "value": self._items[i]
            }

    def _send_insert(self, args: dict, socket: _SockSyncSocket) -> Optional[dict]:
        i = args["index"]
        socket_i = self._get_socket_index(i, socket)
        if socket_i is not None:
            return {
                "index": socket_i,
                "value": self._items[i]
            }
        else:
            self._send_func("set_count", socket)

    def _send_delete(self, args: dict, socket: _SockSyncSocket) -> Optional[dict]:
        i = args["index"]
        socket_i = self._get_socket_index(i, socket)
        if socket_i is not None:
            return {"index": socket_i}
        else:
            self._send_func("set_count", socket)

    def _get_socket_index(self, i: int, socket: _SockSyncSocket) -> Optional[int]:
        page, page_size = self._subscriber_pages[socket]
        if page * page_size <= i < page * page_size + page_size:
            return i - page * page_size
        return None


# class SockSyncModelList(SockSyncList):
#     def __init__(self, name: str, model: Model, query: QuerySet = None):
#         super().__init__(name)
#         self.model: Model = model
#         self.query = query
#         if query is None:
#             self.query = model.objects.all()
#
#         post_save.connect(self._model_post_save, sender=model)
#         post_delete.connect(self._model_post_delete, sender=model)
#
#     def _model_post_save(self, sender, **kwargs):
#         print(kwargs)
#         pass
#
#     def _model_post_delete(self, sender, **kwargs):
#         pass


class RemoteFunction(RemoteGroup):
    def __init__(self, name: str, socket: _SockSyncSocket, subscribe: bool = True):
        super().__init__(name, "function", socket)
        socket._register_function(self)
        self._returns: Dict[str, dict] = {}

        self._register_receive("return", self._recv_return, True, ["id"])
        self._register_send("call", lambda args: {"id": args["id"], "args": args["args"]})

        if subscribe:
            self.subscribe()

    def call(self, **kwargs):
        if not self.subscribed:
            return None

        id_ = str(uuid4())
        self._send_func("call", args={"id": id_, "args": kwargs})

        while id_ not in self._returns:
            time.sleep(.25)

        return_data = self._returns[id_]
        self._returns.pop(id_)

        return return_data

    def _recv_return(self, data: dict, _):
        id_ = data["id"]
        self._returns[id_] = data.get("value", None)


class LocalFunction(LocalGroup):
    def __init__(self, name: str, function: Callable = None):
        super().__init__(name)
        self.function = function

        self._register_receive("call", self._recv_call, True, ["id"])
        self._register_send("return", lambda args, socket: {"id": args["id"], "value": args["value"]})

    def _recv_call(self, data: dict, socket: _SockSyncSocket):
        Thread(target=self._function_call_wrapper, args=(data["id"], data, socket)).start()

    def _function_call_wrapper(self, id_: str, data: dict, socket: _SockSyncSocket):
        self._send_func("return", socket, {"id": id_, "value": self.function(**data.get("args", {}))})
