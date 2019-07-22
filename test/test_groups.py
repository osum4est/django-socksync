from socksync.errors import SockSyncErrors
from socksync.groups import RemoteVariable, LocalVariable
from test import helpers


def test_constructor_subscribe_remote(socket, remote_groups):
    for group in remote_groups:
        assert group.subscribed


def test_subscribe_remote(socket, remote_groups):
    for group in remote_groups:
        group.unsubscribe()

    for group in remote_groups:
        helpers.reset_send(socket)
        group.subscribe()
        assert group.subscribed
        helpers.assert_send_group_func(socket, "subscribe", group)
        helpers.assert_send_call_count(socket, 1)


def test_unsubscribe_remote(socket, remote_groups):
    for group in remote_groups:
        helpers.reset_send(socket)
        group.unsubscribe()
        assert not group.subscribed
        helpers.assert_send_group_func(socket, "unsubscribe", group)
        helpers.assert_send_call_count(socket, 1)


def test_subscribe_local(socket, local_groups):
    for group in local_groups:
        assert len(group.subscribers) == 0
        socket.register_group(group)
        helpers.receive_group_func(socket, "subscribe", group)
        assert socket in group.subscribers
        assert len(group.subscribers) == 1
        helpers.assert_no_send(socket)


def test_unsubscribe_local(socket, local_groups):
    for group in local_groups:
        socket.register_group(group)
        helpers.receive_group_func(socket, "subscribe", group)
        helpers.reset_send(socket)
        helpers.receive_group_func(socket, "unsubscribe", group)
        assert socket not in group.subscribers
        assert len(group.subscribers) == 0
        helpers.assert_no_send(socket)


def test_remote_variable_get(socket):
    var = RemoteVariable("test", socket)
    helpers.reset_send(socket)
    var.get()
    helpers.assert_send_group_func(socket, "get", var)
    helpers.assert_send_call_count(socket, 1)
    assert var.value is None


def test_remote_variable_set(socket):
    var = RemoteVariable("test", socket)
    helpers.reset_send(socket)
    helpers.receive_group_func(socket, "set", var, args={"value": 10})
    helpers.assert_no_send(socket)
    assert var.value == 10


def test_remote_variable_set_unsubscribed(socket):
    var = RemoteVariable("test", socket, False)
    helpers.reset_send(socket)
    helpers.receive_group_func(socket, "set", var, args={"value": 10})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)
    helpers.assert_send_call_count(socket, 1)
    assert var.value is None


def test_local_variable_get(socket):
    var = LocalVariable("test", 10)
    socket.register_group(var)
    helpers.reset_send(socket)
    helpers.receive_group_func(socket, "subscribe", var)
    helpers.receive_group_func(socket, "get", var)
    helpers.assert_send_group_func(socket, "set", var, args={"value": 10})
    helpers.assert_send_call_count(socket, 1)


def test_local_variable_get_unsubscribed(socket):
    var = LocalVariable("test", 10)
    socket.register_group(var)
    helpers.reset_send(socket)
    helpers.receive_group_func(socket, "get", var)
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)
    helpers.assert_send_call_count(socket, 1)


def test_local_variable_set(socket):
    var = LocalVariable("test", 10)
    socket.register_group(var)
    helpers.reset_send(socket)
    helpers.receive_group_func(socket, "subscribe", var)
    var.value = 20
    helpers.assert_send_group_func(socket, "set", var, args={"value": 20})
    helpers.assert_send_call_count(socket, 1)


def test_local_variable_set_unsubscribed(socket):
    var = LocalVariable("test", 10)
    socket.register_group(var)
    var.value = 20
    helpers.assert_no_send(socket)
