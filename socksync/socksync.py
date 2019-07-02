from typing import Callable

from socksync.sockets import SockSyncSocket

on_new_connection: Callable[[SockSyncSocket], None]

# def register_model(model: Model, name: str = None):
#     """
#     Registers a django model as a SockSync list. By default it will allow a client to access the whole model or a single
#     row via it's id. This is done by using django signals, so only database updates done by django will be recognized.
#     :param model: The model to register.
#     :param name: The name of the SockSync list. If None the model's default name will be used.
#     """
#
#     if name is None:
#         name = model.__name__
#
#     register_list(name, SockSyncModelList(model))
#
#
# def register_list(ss_list: SockSyncList):
#     registry.lists[ss_list.name] = ss_list

# TODO: Paging, filtering
