import json

from socksync.groups import Group
from socksync.utils import dict_without_none


def receive_group_func(socket, func: str, group: Group, args: dict = None):
    receive_func(socket, func, group.type, group.name, args)


def receive_func(socket, func: str, type_: str = None, name: str = None, args: dict = None):
    socket.receive(
        json.dumps(dict_without_none({"func": func, "type": type_, "name": name, **({} if args is None else args)})))


def reset_send(socket):
    return socket.send.reset_mock()


def assert_send_call_count(socket, call_count):
    assert socket.send.call_count == call_count


def assert_send_group_func(socket, func: str, group: Group, args: dict = None):
    assert_send_func(socket, func, group.type, group.name, args)


def assert_send_func(socket, func: str, type_: str = None, name: str = None, args: dict = None):
    data = json.loads(socket.send.call_args[0][0])
    length = 1

    assert data["func"] == func
    if name is not None:
        length += 1
        assert data["name"] == name
    if type_ is not None:
        length += 1
        assert data["type"] == type_
    if args is not None:
        length += len(args)
        for k, v in args.items():
            assert data[k] == v

    assert len(data) == length


def assert_send_error(socket, error_code: int):
    data = json.loads(socket.send.call_args[0][0])
    assert data["func"] == "error"
    assert data["error_code"] == error_code
    assert len(data) == 3


def assert_no_send(socket):
    socket.send.assert_not_called()
