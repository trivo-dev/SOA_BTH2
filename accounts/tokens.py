import secrets
import time
import jwt
from django.conf import settings


def issue_token(user):
    now = int(time.time())
    # Compact claims keep this HS256 token within the assignment's VARCHAR(255).
    return jwt.encode(
        {"sub": str(user.pk), "iat": now, "exp": now + settings.JWT_TTL_SECONDS,
         "jti": secrets.token_hex(8)},
        settings.SECRET_KEY, algorithm="HS256",
    )


def decode_token(token):
    return jwt.decode(
        token, settings.SECRET_KEY, algorithms=["HS256"],
        options={"require": ["sub", "iat", "exp", "jti"]},
    )
