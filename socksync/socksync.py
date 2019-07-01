from django.db.models import Model

from socksync import registry
from socksync.socksync_list import SockSyncList
from socksync.socksync_model_list import SockSyncModelList
from socksync.socksync_variable import SockSyncVariable


def register_variable(var: SockSyncVariable):
    registry.variables[var.name] = var


def register_model(model: Model, name: str = None):
    """
    Registers a django model as a SockSync list. By default it will allow a client to access the whole model or a single
    row via it's id. This is done by using django signals, so only database updates done by django will be recognized.
    :param model: The model to register.
    :param name: The name of the SockSync list. If None the model's default name will be used.
    """

    if name is None:
        name = model.__name__

    register_list(name, SockSyncModelList(model))


def register_list(ss_list: SockSyncList):
    registry.lists[ss_list.name] = ss_list


# TODO: Paging, filtering
# TODO: Type hint everything
# TODO: Two way binding
# TODO: Web dashboard showing all registered vars
