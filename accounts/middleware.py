import jwt
from django.http import JsonResponse
from django.utils.crypto import constant_time_compare
from .models import User
from .tokens import decode_token


class JWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Only the explicitly marked login view is public.
        if getattr(view_func, "public_api", False):
            return None
        parts = request.headers.get("Authorization", "").split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return self.unauthorized("Thiếu hoặc sai Authorization: Bearer <token>.")
        token = parts[1]
        try:
            claims = decode_token(token)
            subject = claims["sub"]
            if not isinstance(subject, str) or not subject.isascii() or not subject.isdigit() or len(subject) > 10:
                raise ValueError("Invalid subject")
            user = User.objects.get(pk=int(subject))
            if not constant_time_compare(user.Token, token):
                return self.unauthorized("Token đã bị thay thế. Hãy đăng nhập lại.")
        except jwt.ExpiredSignatureError:
            return self.unauthorized("Token đã hết hạn.")
        except (jwt.InvalidTokenError, User.DoesNotExist, ValueError, TypeError, OverflowError):
            return self.unauthorized("Token không hợp lệ.")
        request.api_user = user
        request.jwt_claims = claims
        return None

    @staticmethod
    def unauthorized(message):
        response = JsonResponse({"error": message}, status=401)
        response["WWW-Authenticate"] = "Bearer"
        return response
