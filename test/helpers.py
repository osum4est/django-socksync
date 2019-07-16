import json
from typing import Optional

from socksync.utils import dict_without_none


def receive_func(socket, func: str, type_: str = None, name: str = None):
    socket.receive(json.dumps(dict_without_none({"func": func, "type": type_, "name": name})))


def assert_send_func(socket, func: str, call_count: Optional[int] = 1):
    if call_count is not None:
        assert socket.send.call_count == call_count
    data = json.loads(socket.send.call_args[0][0])
    assert data["func"] == func


def assert_send_error(socket, error_code: int, call_count: Optional[int] = 1):
    if call_count is not None:
        assert socket.send.call_count == call_count
    data = json.loads(socket.send.call_args[0][0])
    assert data["func"] == "error"
    assert data["error_code"] == error_code


def assert_no_send(socket):
    socket.send.assert_not_called()
