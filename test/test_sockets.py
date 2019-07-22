import json

import pytest

from socksync import socksync
from socksync.errors import SockSyncErrors
from socksync.groups import LocalVariable, LocalList, LocalFunction
from test import helpers


@pytest.mark.parametrize("group", [LocalVariable("g"), LocalList("g"), LocalFunction("g")])
def test_register(socket, group):
    socket.register_group(group)
    helpers.receive_group_func(socket, "subscribe", group)
    helpers.assert_no_send(socket)


@pytest.mark.parametrize("group", [LocalVariable("g"), LocalList("g"), LocalFunction("g")])
def test_not_registered(socket, group):
    socket.register_group(group)
    helpers.receive_func(socket, "subscribe", group.type, "missing")
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_NAME)
    helpers.assert_send_call_count(socket, 1)


def test_connect(socket):
    socket.connect()
    socket.accept.assert_called_once()


def test_connect_handler(socket, f):
    socksync.add_new_connection_handler(f)
    socket.connect()
    f.assert_called_once_with(socket)


@pytest.mark.parametrize("group", [LocalVariable("g"), LocalList("g"), LocalFunction("g")])
def test_disconnect(socket, group):
    socket.register_group(group)
    socket.disconnect(None)
    helpers.receive_group_func(socket, "subscribe", group)
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_NAME)


@pytest.mark.parametrize("group", [LocalVariable("g"), LocalList("g"), LocalFunction("g")])
def test_disconnect_then_add(socket, group):
    socket.register_group(group)
    socket.disconnect(None)
    socket.register_group(group)
    helpers.receive_group_func(socket, "subscribe", group)
    helpers.assert_no_send(socket)


def test_receive_empty(socket):
    socket.receive("")
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_JSON)


def test_receive_invalid_json(socket):
    socket.receive("{{ i am in} valid:")
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_JSON)


def test_receive_no_func(socket):
    socket.receive(json.dumps({}))
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)


def test_receive_invalid_func(socket):
    helpers.receive_func(socket, "invalid")
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_TYPE)


def test_receive_no_type(socket):
    helpers.receive_func(socket, "subscribe", name="a")
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_TYPE)


def test_receive_invalid_type(socket):
    helpers.receive_func(socket, "subscribe", "invalid", "a")
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_TYPE)


def test_receive_no_name(socket):
    helpers.receive_func(socket, "subscribe", "var")
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_NAME)


def test_receive_error(socket):
    helpers.receive_func(socket, "error", args={"error_code": 0, "message": "error"})
    helpers.assert_no_send(socket)


def test_receive_unsubscribe_all(socket, local_groups):
    for g in local_groups:
        socket.register_group(g)
    helpers.receive_func(socket, "unsubscribe_all")
    helpers.assert_no_send(socket)
    for g in local_groups:
        assert len(g.subscribers) == 0


def test_unsubscribe_all(socket, remote_groups):
    helpers.reset_send(socket)
    socket.unsubscribe_all()
    helpers.assert_send_func(socket, "unsubscribe_all")
    helpers.assert_send_call_count(socket, 1)
    for g in remote_groups:
        assert not g.subscribed
