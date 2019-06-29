from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class SockSyncConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            "test_group",
            self.channel_name
        )

        self.accept()

    def disconnect(self, code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        async_to_sync(self.channel_layer.group_send)(
            "test_group",
            {
                'type': 'test', 'hi': 'hi man'
            }
        )

    def test(self, event):
        self.send(text_data=event['hi'])
