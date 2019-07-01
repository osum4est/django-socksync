from socksync.socksync_socket_group import SockSyncSocketGroup


class SockSyncList(SockSyncSocketGroup):
    value = []

    def get(self, index: int) -> object:
        return self.value[index]

    def set(self, index: int, value: object):
        self.value[index] = value
        # TODO: Update subscribers
