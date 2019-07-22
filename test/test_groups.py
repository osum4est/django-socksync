from socksync.errors import SockSyncErrors
from test import helpers


def test_constructor_subscribe_remote(socket, remote_groups):
    for group in remote_groups:
        assert group.subscribed


def test_subscribe_remote(socket, remote_groups):
    for group in remote_groups:
        group.unsubscribe()

    helpers.reset_send(socket)
    for group in remote_groups:
        group.subscribe()
        assert group.subscribed
        helpers.assert_send_group_func(socket, "subscribe", group)


def test_unsubscribe_remote(socket, remote_groups):
    for group in remote_groups:
        group.unsubscribe()
        assert not group.subscribed
        helpers.assert_send_group_func(socket, "unsubscribe", group)


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
        helpers.receive_group_func(socket, "unsubscribe", group)
        assert socket not in group.subscribers
        assert len(group.subscribers) == 0
        helpers.assert_no_send(socket)


def test_remote_variable_get(socket, remote_variable):
    remote_variable.get()
    helpers.assert_send_group_func(socket, "get", remote_variable)
    assert remote_variable.value is None


def test_remote_variable_set(socket, remote_variable):
    helpers.receive_group_func(socket, "set", remote_variable, args={"value": 10})
    helpers.assert_no_send(socket)
    assert remote_variable.value == 10


def test_remote_variable_set_unsubscribed(socket, remote_variable_unsubscribed):
    helpers.receive_group_func(socket, "set", remote_variable_unsubscribed, args={"value": 10})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)
    assert remote_variable_unsubscribed.value is None


def test_local_variable_get(socket, local_variable):
    helpers.receive_group_func(socket, "subscribe", local_variable)
    helpers.receive_group_func(socket, "get", local_variable)
    helpers.assert_send_group_func(socket, "set", local_variable, args={"value": 10})


def test_local_variable_get_unsubscribed(socket, local_variable):
    helpers.receive_group_func(socket, "get", local_variable)
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)


def test_local_variable_set(socket, local_variable):
    helpers.receive_group_func(socket, "subscribe", local_variable)
    local_variable.value = 20
    helpers.assert_send_group_func(socket, "set", local_variable, args={"value": 20})


def test_local_variable_set_unsubscribed(socket, local_variable):
    local_variable.value = 20
    helpers.assert_no_send(socket)


def test_remote_list_get(socket, remote_list):
    remote_list.get()
    helpers.assert_send_group_func(socket, "get", remote_list, args={"page": 0, "page_size": 5})
    assert len(list(remote_list.items)) == 0
    assert remote_list.page == 0
    assert remote_list.page_size == 5
    assert remote_list.count == 0


def test_remote_list_set_all(socket, remote_list):
    helpers.init_remote_list(socket, remote_list)
    assert list(remote_list.items) == [1, 2, 3]
    assert remote_list.page == 1
    assert remote_list.page_size == 3
    assert remote_list.count == 20


def test_remote_list_set_all_unsubscribed(socket, remote_list_unsubscribed):
    helpers.init_remote_list(socket, remote_list_unsubscribed, False)
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)
    assert len(list(remote_list_unsubscribed.items)) == 0
    assert remote_list_unsubscribed.page == 0
    assert remote_list_unsubscribed.page_size == 5
    assert remote_list_unsubscribed.count == 0


def test_remote_list_set_all_missing_field(socket, remote_list):
    helpers.receive_group_func(socket, "set_all", remote_list)
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_MISSING_FIELD)


def test_remote_list_set_count(socket, remote_list):
    helpers.receive_group_func(socket, "set_count", remote_list, args={"total_item_count": 20})
    helpers.assert_no_send(socket)
    assert remote_list.count == 20


def test_remote_list_set_count_unsubscribed(socket, remote_list_unsubscribed):
    helpers.receive_group_func(socket, "set_count", remote_list_unsubscribed, args={"total_item_count": 20})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)
    assert remote_list_unsubscribed.count == 0


def test_remote_list_set(socket, remote_list):
    helpers.init_remote_list(socket, remote_list)
    helpers.receive_group_func(socket, "set", remote_list, args={"index": 0, "value": "test"})
    helpers.assert_no_send(socket)
    assert list(remote_list.items) == ["test", 2, 3]


def test_remote_list_set_unsubscribed(socket, remote_list_unsubscribed):
    helpers.receive_group_func(socket, "set", remote_list_unsubscribed, args={"index": 0, "value": "test"})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)
    assert len(list(remote_list_unsubscribed.items)) == 0


def test_remote_list_set_out_of_bounds(socket, remote_list):
    helpers.receive_group_func(socket, "set", remote_list, args={"index": 0, "value": 1})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_BAD_INDEX)


def test_remote_list_insert(socket, remote_list):
    helpers.init_remote_list(socket, remote_list)
    helpers.receive_group_func(socket, "insert", remote_list, args={"index": 2, "value": "test"})
    helpers.assert_no_send(socket)
    assert list(remote_list.items) == [1, 2, "test", 3]


def test_remote_list_insert_unsubscribed(socket, remote_list_unsubscribed):
    helpers.receive_group_func(socket, "insert", remote_list_unsubscribed, args={"index": 2, "value": "test"})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)
    assert len(list(remote_list_unsubscribed.items)) == 0


def test_remote_list_delete(socket, remote_list):
    helpers.init_remote_list(socket, remote_list)
    helpers.receive_group_func(socket, "delete", remote_list, args={"index": 2})
    helpers.assert_no_send(socket)
    assert list(remote_list.items) == [1, 2]


def test_remote_list_delete_unsubscribed(socket, remote_list_unsubscribed):
    helpers.receive_group_func(socket, "delete", remote_list_unsubscribed, args={"index": 2})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)
    assert len(list(remote_list_unsubscribed.items)) == 0


def test_remote_list_delete_out_of_bounds(socket, remote_list):
    helpers.init_remote_list(socket, remote_list)
    helpers.receive_group_func(socket, "delete", remote_list, args={"index": 3})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_BAD_INDEX)
    assert list(remote_list.items) == [1, 2, 3]
