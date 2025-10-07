from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser, User
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs


class JWTAuthMiddleware:
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Get the token from query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        # Authenticate the user
        scope['user'] = await self.get_user_from_token(token)
        
        return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token):
        """
        Validate JWT token and return the user.
        """
        if not token:
            return AnonymousUser()

        try:
            # Decode the token
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            # Get the user
            user = User.objects.get(id=user_id)
            return user
        except (InvalidToken, TokenError, User.DoesNotExist):
            return AnonymousUser()
