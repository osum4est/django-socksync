import json
import time
from threading import Thread

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
    helpers.receive_group_func(socket, "set", remote_variable, {"value": 10})
    helpers.assert_no_send(socket)
    assert remote_variable.value == 10


def test_remote_variable_set_unsubscribed(socket, remote_variable_unsubscribed):
    helpers.receive_group_func(socket, "set", remote_variable_unsubscribed, {"value": 10})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)
    assert remote_variable_unsubscribed.value is None


def test_local_variable_get(socket, local_variable):
    helpers.receive_group_func(socket, "get", local_variable)
    helpers.assert_send_group_func(socket, "set", local_variable, {"value": 10})


def test_local_variable_get_unsubscribed(socket, local_variable_unsubscribed):
    helpers.receive_group_func(socket, "get", local_variable_unsubscribed)
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)


def test_local_variable_set(socket, local_variable):
    local_variable.value = 20
    helpers.assert_send_group_func(socket, "set", local_variable, {"value": 20})


def test_local_variable_set_unsubscribed(socket, local_variable_unsubscribed):
    local_variable_unsubscribed.value = 20
    helpers.assert_no_send(socket)


def test_remote_list_get(socket, remote_list):
    remote_list.get()
    helpers.assert_send_group_func(socket, "get", remote_list, {"page": 0, "page_size": 5})
    assert len(list(remote_list.items)) == 0
    assert remote_list.page == 0
    assert remote_list.page_size == 5
    assert remote_list.count == 0


def test_remote_list_get_page_0(socket, remote_list):
    helpers.receive_group_func(socket, "set_count", remote_list, {"total_item_count": 10})
    remote_list.get_page(0)
    helpers.assert_send_group_func(socket, "get", remote_list, {"page": 0, "page_size": 5})
    assert len(list(remote_list.items)) == 0


def test_remote_list_get_page_1(socket, remote_list):
    helpers.receive_group_func(socket, "set_count", remote_list, {"total_item_count": 10})
    remote_list.get_page(1)
    helpers.assert_send_group_func(socket, "get", remote_list, {"page": 1, "page_size": 5})
    assert len(list(remote_list.items)) == 0


def test_remote_list_pages(socket, remote_list):
    remote_list.get_page(1)
    helpers.receive_group_func(socket, "set_count", remote_list, {"total_item_count": 10})
    assert remote_list.pages == 2
    helpers.receive_group_func(socket, "set_count", remote_list, {"total_item_count": 14})
    assert remote_list.pages == 3
    helpers.receive_group_func(socket, "set_count", remote_list, {"total_item_count": 6})
    assert remote_list.pages == 2


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
    helpers.receive_group_func(socket, "set_count", remote_list, {"total_item_count": 50})
    helpers.assert_no_send(socket)
    assert remote_list.count == 50


def test_remote_list_set_count_unsubscribed(socket, remote_list_unsubscribed):
    helpers.receive_group_func(socket, "set_count", remote_list_unsubscribed, {"total_item_count": 50})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)
    assert remote_list_unsubscribed.count == 0


def test_remote_list_set(socket, remote_list):
    helpers.init_remote_list(socket, remote_list)
    helpers.receive_group_func(socket, "set", remote_list, {"index": 0, "value": "test"})
    helpers.assert_no_send(socket)
    assert list(remote_list.items) == ["test", 2, 3]
    assert remote_list.count == 20


def test_remote_list_set_unsubscribed(socket, remote_list_unsubscribed):
    helpers.receive_group_func(socket, "set", remote_list_unsubscribed, {"index": 0, "value": "test"})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)
    assert len(list(remote_list_unsubscribed.items)) == 0


def test_remote_list_set_out_of_bounds(socket, remote_list):
    helpers.init_remote_list(socket, remote_list)
    helpers.receive_group_func(socket, "set", remote_list, {"index": 3, "value": 1})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_BAD_INDEX)
    assert list(remote_list.items) == [1, 2, 3]


def test_remote_list_insert(socket, remote_list):
    helpers.init_remote_list(socket, remote_list)
    helpers.receive_group_func(socket, "insert", remote_list, {"index": 2, "value": "test"})
    helpers.assert_no_send(socket)
    assert list(remote_list.items) == [1, 2, "test", 3]
    assert remote_list.count == 20


def test_remote_list_insert_unsubscribed(socket, remote_list_unsubscribed):
    helpers.receive_group_func(socket, "insert", remote_list_unsubscribed, {"index": 2, "value": "test"})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)
    assert len(list(remote_list_unsubscribed.items)) == 0


def test_remote_list_delete(socket, remote_list):
    helpers.init_remote_list(socket, remote_list)
    helpers.receive_group_func(socket, "delete", remote_list, {"index": 2})
    helpers.assert_no_send(socket)
    assert list(remote_list.items) == [1, 2]
    assert remote_list.count == 20


def test_remote_list_delete_unsubscribed(socket, remote_list_unsubscribed):
    helpers.receive_group_func(socket, "delete", remote_list_unsubscribed, {"index": 2})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)
    assert len(list(remote_list_unsubscribed.items)) == 0


def test_remote_list_delete_out_of_bounds(socket, remote_list):
    helpers.init_remote_list(socket, remote_list)
    helpers.receive_group_func(socket, "delete", remote_list, {"index": 3})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_BAD_INDEX)
    assert list(remote_list.items) == [1, 2, 3]
    assert remote_list.count == 20


def test_local_list_get_page_0(socket, local_list):
    helpers.receive_group_func(socket, "get", local_list, {"page": 0, "page_size": 2})
    helpers.assert_send_group_func(socket, "set_all", local_list,
                                   {"page": 0, "page_size": 2, "total_item_count": 3, "items": [1, 2]})


def test_local_list_get_page_1(socket, local_list):
    helpers.receive_group_func(socket, "get", local_list, {"page": 1, "page_size": 2})
    helpers.assert_send_group_func(socket, "set_all", local_list,
                                   {"page": 1, "page_size": 2, "total_item_count": 3, "items": [3]})


def test_local_list_get_unsubscribed(socket, local_list_unsubscribed):
    helpers.receive_group_func(socket, "get", local_list_unsubscribed, {"page": 0, "page_size": 5})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)


def test_local_list_set_count_insert(socket, local_list):
    helpers.receive_group_func(socket, "get", local_list, {"page": 0, "page_size": 2})
    helpers.reset_send(socket)
    local_list.append("test")
    helpers.assert_send_group_func(socket, "set_count", local_list, {"total_item_count": 4})


def test_local_list_set_count_delete(socket, local_list):
    helpers.receive_group_func(socket, "get", local_list, {"page": 0, "page_size": 2})
    helpers.reset_send(socket)
    local_list.delete(2)
    helpers.assert_send_group_func(socket, "set_count", local_list, {"total_item_count": 2})


def test_local_list_set_count_unsubscribed(socket, local_list_unsubscribed):
    local_list_unsubscribed.append("test")
    local_list_unsubscribed.delete(2)
    helpers.assert_no_send(socket)


def test_local_list_set(socket, local_list):
    local_list.set(0, "test")
    helpers.assert_send_group_func(socket, "set", local_list, {"index": 0, "value": "test"})


def test_local_list_set_out_of_bounds(socket, local_list):
    helpers.receive_group_func(socket, "get", local_list, {"page": 0, "page_size": 2})
    helpers.reset_send(socket)
    local_list.set(2, "test")
    helpers.assert_no_send(socket)


def test_local_list_set_unsubscribed(socket, local_list_unsubscribed):
    local_list_unsubscribed.set(0, "test")
    helpers.assert_no_send(socket)


def test_local_list_insert(socket, local_list):
    local_list.insert(0, "test")
    helpers.assert_send_group_func(socket, "set_count", local_list, {"total_item_count": 4}, True)
    helpers.assert_send_group_func(socket, "insert", local_list, {"index": 0, "value": "test"})


def test_local_list_insert_paged(socket, local_list):
    helpers.receive_group_func(socket, "get", local_list, {"page": 1, "page_size": 2})
    helpers.reset_send(socket)
    local_list.insert(0, "test")
    helpers.assert_send_group_func(socket, "set_count", local_list, {"total_item_count": 4}, True)
    helpers.assert_send_group_func(socket, "delete", local_list, {"index": 1}, True)
    helpers.assert_send_group_func(socket, "insert", local_list, {"index": 0, "value": 2})


def test_local_list_insert_unsubscribed(socket, local_list_unsubscribed):
    local_list_unsubscribed.insert(0, "test")
    helpers.assert_no_send(socket)


def test_local_list_delete(socket, local_list):
    local_list.delete(0)
    helpers.assert_send_group_func(socket, "set_count", local_list, {"total_item_count": 2}, True)
    helpers.assert_send_group_func(socket, "delete", local_list, {"index": 0})


def test_local_list_delete_paged(socket, local_list):
    local_list.insert(0, 10)
    local_list.insert(0, 11)
    local_list.insert(0, 12)
    helpers.receive_group_func(socket, "get", local_list, {"page": 1, "page_size": 2})
    helpers.reset_send(socket)
    local_list.delete(0)
    helpers.assert_send_group_func(socket, "set_count", local_list, {"total_item_count": 5}, True)
    helpers.assert_send_group_func(socket, "delete", local_list, {"index": 0}, True)
    helpers.assert_send_group_func(socket, "insert", local_list, {"index": 1, "value": 2})


def test_local_list_delete_unsubscribed(socket, local_list_unsubscribed):
    local_list_unsubscribed.delete(0)
    helpers.assert_no_send(socket)


def test_remote_function_return_invalid_id(socket, remote_function):
    helpers.receive_group_func(socket, "return", remote_function, {"id": "test_id"})
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_BAD_ID)


def test_remote_function_call(socket, remote_function):
    result = []
    t = Thread(target=lambda: result.append(remote_function.call(arg1=0, arg2="test")))
    t.start()

    timeout = time.time() + 10
    while socket.send.call_count == 0:
        time.sleep(.1)
        assert time.time() < timeout

    call_id = json.loads(socket.send.call_args[0][0])["id"]
    helpers.assert_send_group_func(socket, "call", remote_function,
                                   {"id": call_id, "args": {"arg1": 0, "arg2": "test"}})
    helpers.receive_group_func(socket, "return", remote_function, {"id": call_id, "value": "test_return"})
    t.join()
    assert result[0] == "test_return"


def test_remote_function_call_unsubscribed(socket, remote_function_unsubscribed):
    remote_function_unsubscribed.call(arg1=0, arg2="test")
    helpers.assert_no_send(socket)


def test_local_function_call(socket, local_function, f):
    f.return_value = "test_return"
    helpers.receive_group_func(socket, "call", local_function, {"id": "test_id", "args": {"arg1": 0, "arg2": "test"}})
    f.assert_called_once_with(**{"arg1": 0, "arg2": "test"})
    helpers.assert_send_group_func(socket, "return", local_function, {"id": "test_id", "value": "test_return"})


def test_local_function_call_unsubscribed(socket, local_function_unsubscribed, f):
    helpers.receive_group_func(socket, "call", local_function_unsubscribed,
                               {"id": "test_id", "args": {"arg1": 0, "arg2": "test"}})
    f.assert_not_called()
    helpers.assert_send_error(socket, SockSyncErrors.ERROR_INVALID_FUNC)
