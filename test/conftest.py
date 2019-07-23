from pytest import fixture

from socksync.groups import LocalFunction, LocalVariable, LocalList, RemoteFunction, RemoteVariable, RemoteList
from socksync.sockets import SockSyncSocket
from test import helpers


@fixture
def socket(mocker):
    mocker.patch("channels.generic.websocket.WebsocketConsumer.send")
    mocker.patch("channels.generic.websocket.WebsocketConsumer.accept")
    return SockSyncSocket(scope=None)


@fixture
def f(mocker):
    return mocker.stub()


@fixture
def local_groups():
    return [LocalVariable("a"), LocalVariable("b"), LocalList("b"), LocalList("c"), LocalFunction("c"),
            LocalFunction("d")]


@fixture
def remote_groups(socket):
    groups = [RemoteVariable("a", socket), RemoteVariable("b", socket), RemoteList("b", socket),
              RemoteList("c", socket), RemoteFunction("c", socket), RemoteFunction("d", socket)]
    helpers.reset_send(socket)
    return groups


@fixture
def remote_variable(socket):
    var = RemoteVariable("test", socket)
    helpers.reset_send(socket)
    return var


@fixture
def remote_variable_unsubscribed(socket):
    var = RemoteVariable("test", socket, False)
    helpers.reset_send(socket)
    return var


@fixture
def local_variable(socket):
    var = LocalVariable("test", 10)
    socket.register_group(var)
    helpers.receive_group_func(socket, "subscribe", var)
    return var


@fixture
def local_variable_unsubscribed(socket):
    var = LocalVariable("test", 10)
    socket.register_group(var)
    return var


@fixture
def remote_list(socket):
    lst = RemoteList("test", socket, 5)
    helpers.reset_send(socket)
    return lst


@fixture
def remote_list_unsubscribed(socket):
    lst = RemoteList("test", socket, 5, False)
    helpers.reset_send(socket)
    return lst


@fixture
def local_list(socket):
    lst = LocalList("test", [1, 2, 3])
    socket.register_group(lst)
    helpers.receive_group_func(socket, "subscribe", lst)
    return lst


@fixture
def local_list_unsubscribed(socket):
    lst = LocalList("test", [1, 2, 3])
    socket.register_group(lst)
    return lst
