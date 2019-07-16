from pytest import fixture

from socksync.groups import LocalFunction, LocalVariable, LocalList, RemoteFunction, RemoteVariable, RemoteList
from socksync.sockets import SockSyncSocket


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
    return [RemoteVariable("a", socket), RemoteVariable("b", socket), RemoteList("b", socket),
            RemoteList("c", socket), RemoteFunction("c", socket), RemoteFunction("d", socket)]
