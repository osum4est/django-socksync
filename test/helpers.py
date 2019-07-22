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


def assert_send_group_func(socket, func: str, group: Group, args: dict = None):
    assert_send_func(socket, func, group.type, group.name, args)


def assert_send_func(socket, func: str, type_: str = None, name: str = None, args: dict = None):
    assert socket.send.call_count == 1
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
    reset_send(socket)


def assert_send_error(socket, error_code: int):
    assert socket.send.call_count == 1
    data = json.loads(socket.send.call_args[0][0])
    assert data["func"] == "error"
    assert data["error_code"] == error_code
    assert len(data) == 3
    reset_send(socket)


def assert_no_send(socket):
    socket.send.assert_not_called()
    reset_send(socket)


def init_remote_list(socket, remote_list, assert_success=True):
    receive_group_func(socket, "set_all", remote_list,
                       args={"page": 1, "page_size": 3, "total_item_count": 20, "items": [1, 2, 3]})

    if assert_success:
        assert_no_send(socket)
        reset_send(socket)
