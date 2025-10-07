import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Conversation, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        
        # Check if user is authenticated
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return
        
        # Check if user is participant in conversation
        is_participant = await self.is_user_participant(user, self.conversation_id)
        if not is_participant:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            message_text = data.get('message', '')
            
            # Save message to database
            message = await self.save_message(
                self.scope['user'],
                self.conversation_id,
                message_text
            )
            
            # Get message data with related fields
            message_data = await self.get_message_data(message.id)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_data
                }
            )
        elif message_type == 'typing':
            # Broadcast typing indicator
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.scope['user'].id,
                    'username': self.scope['user'].username,
                    'is_typing': data.get('is_typing', False)
                }
            )
    
    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message
        }))
    
    # Receive typing indicator from room group
    async def typing_indicator(self, event):
        # Don't send typing indicator to the user who is typing
        if event['user_id'] != self.scope['user'].id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    @database_sync_to_async
    def is_user_participant(self, user, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            return user in conversation.participants.all()
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, user, conversation_id, text):
        conversation = Conversation.objects.get(id=conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            text=text
        )
        
        # Update conversation's updated_at timestamp
        conversation.save()
        
        return message
    
    @database_sync_to_async
    def get_message_data(self, message_id):
        """Get message data with related fields for serialization"""
        message = Message.objects.select_related('sender', 'sender__profile').get(id=message_id)
        return {
            'id': message.id,
            'text': message.text,
            'sender': {
                'id': message.sender.id,
                'username': message.sender.username,
                'profile': {
                    'avatar': message.sender.profile.avatar.url if message.sender.profile.avatar else None
                }
            },
            'created_at': message.created_at.isoformat(),
            'is_read': message.is_read
        }
