import base64
import binascii
import json
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from .models import User
from .tokens import issue_token

DUMMY_HASH = make_password("dummy-password-for-timing")


@csrf_exempt
@require_POST
def login(request):
    # No cookies/session authentication: clients explicitly send a bearer token.
    if request.content_type != "application/json":
        return JsonResponse({"error": "Sử dụng Content-Type: application/json."}, status=415)
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError()
        username, encoded = data.get("userName"), data.get("password")
        if not isinstance(username, str) or not username.strip() or len(username) > 255:
            raise ValueError()
        if not isinstance(encoded, str) or not encoded or len(encoded) > 4096:
            raise ValueError()
        password = base64.b64decode(encoded, validate=True).decode("utf-8")
        if not password:
            raise ValueError()
    except (ValueError, UnicodeError, binascii.Error):
        return JsonResponse({"error": "Cần userName và password được mã hóa Base64 hợp lệ."}, status=400)
    user = User.objects.filter(UserName=username).first()
    valid = check_password(password, user.Password if user else DUMMY_HASH)
    if not user or not valid:
        return JsonResponse({"error": "Sai tài khoản hoặc mật khẩu."}, status=401)
    token = issue_token(user)
    if len(token) > 255:
        return JsonResponse({"error": "Token vượt giới hạn lưu trữ."}, status=500)
    user.Token = token
    user.save(update_fields=["Token"])
    response = JsonResponse({"token": token, "tokenType": "Bearer", "expiresIn": settings.JWT_TTL_SECONDS})
    response["Cache-Control"] = "no-store"
    return response


login.public_api = True


@require_GET
def auth(request):
    response = JsonResponse({
        "authenticated": True,
        "user": {"IdUser": request.api_user.pk, "UserName": request.api_user.UserName},
        "claims": request.jwt_claims,
    })
    response["Cache-Control"] = "no-store"
    return response


@require_GET
def hello(request):
    return JsonResponse({"message": "Hello World"})
