# app/utils/jwt.py
import os
import jwt
from datetime import datetime, timedelta


def generate_jwt_token(uuid):
    encoded_jwt = jwt.encode(
        {
            "sub": uuid,
            "exp": datetime.now() + timedelta(minutes=15),
        },
        os.getenv("JWT_SECRET_KEY"),
        algorithm="HS256",
    )

    return encoded_jwt


def parse_token(token, secret):
    """
    Tries to decode a jwt token
    if success returns: True, uuid to next form
    else returns False
    """
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return True, payload["sub"] # This returns the sub value, change if needed.
    except jwt.ExpiredSignatureError:
        return False, ""
    except jwt.InvalidTokenError:
        return False, ""


def generate_next_url(uuid):
    """Generate redirect url"""
    secret = generate_jwt_token(uuid)
    accept_url = f"{os.getenv("NEXT_FORM_URL")}?secret={secret}"

    return accept_url
