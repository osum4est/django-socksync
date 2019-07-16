from socksync import socksync


def test_add_handler(socket, f):
    socksync.add_new_connection_handler(f)
    socket.connect()
    f.assert_called_once_with(socket)


def test_add_remove_handler(socket, f):
    socksync.add_new_connection_handler(f)
    socksync.remove_new_connection_handler(f)
    socket.connect()
    f.assert_not_called()


def test_remove_handler(socket, f):
    socksync.remove_new_connection_handler(f)
    socket.connect()
    f.assert_not_called()
