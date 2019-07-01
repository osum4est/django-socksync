from django.db.models.signals import post_save

from socksync.socksync_list import SockSyncList


class SockSyncModelList(SockSyncList):
    def __init__(self, model):
        self.model = model
        post_save.connect(self._model_post_save, sender=model)

    def get(self, index: int) -> object:
        pass

    def set(self, index: int, value: object):
        pass

    def _model_post_save(self):
        pass

