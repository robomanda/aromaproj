import json
from channels.generic.websocket import AsyncWebsocketConsumer


class OrderNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("orders", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("orders", self.channel_name)

    async def receive(self, text_data):
        pass  # Optional — not used in this case

    # 👇 This is what handles the message from the view
    async def send_order_notification(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message']
        }))
