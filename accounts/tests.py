import base64
import time
import jwt
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.test import TestCase
from .models import User


class APITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(UserName="admin", Password=make_password("123456"))

    def login(self, password="123456"):
        return self.client.post("/", {
            "userName": "admin", "password": base64.b64encode(password.encode()).decode()
        }, content_type="application/json")

    def test_flow_and_storage(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        token = response.json()["token"]
        self.assertLessEqual(len(token), 255)
        self.user.refresh_from_db()
        self.assertEqual(self.user.Token, token)
        self.assertNotEqual(self.user.Password, "123456")
        headers = {"HTTP_AUTHORIZATION": "Bearer " + token}
        self.assertEqual(self.client.get("/auth", **headers).json()["user"]["UserName"], "admin")
        self.assertEqual(self.client.get("/hello", **headers).json(), {"message": "Hello World"})

    def test_bad_credentials(self):
        self.assertEqual(self.login("wrong").status_code, 401)
        self.assertEqual(self.client.post("/", {"userName": "missing", "password": "MTIzNDU2"},
                                          content_type="application/json").status_code, 401)

    def test_invalid_bodies(self):
        for body in ["{", "[]", "null", "{}", '{"userName":"admin","password":"***"}',
                     '{"userName":"admin","password":123}']:
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/", body, content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/", {}).status_code, 415)
        self.assertEqual(self.client.get("/").status_code, 405)

    def test_missing_and_malformed_tokens(self):
        for path in ["/auth", "/hello"]:
            for header in ["", "Basic abc", "Bearer", "Bearer a b", "Bearer nonsense"]:
                with self.subTest(path=path, header=header):
                    self.assertEqual(self.client.get(path, HTTP_AUTHORIZATION=header).status_code, 401)

    def test_replaced_token(self):
        first = self.login().json()["token"]
        second = self.login().json()["token"]
        self.assertNotEqual(first, second)
        self.assertEqual(self.client.get("/auth", HTTP_AUTHORIZATION="Bearer " + first).status_code, 401)

    def test_invalid_signed_tokens(self):
        now = int(time.time())
        valid = {"sub": str(self.user.pk), "iat": now, "exp": now + 60, "jti": "test"}
        cases = [
            ({**valid, "exp": now - 60}, settings.SECRET_KEY, "HS256"),
            (valid, "wrong-secret-that-is-at-least-32-characters", "HS256"),
            (valid, settings.SECRET_KEY, "HS384"),
            ({"sub": str(self.user.pk)}, settings.SECRET_KEY, "HS256"),
            ({**valid, "sub": "999999"}, settings.SECRET_KEY, "HS256"),
            ({**valid, "sub": "x" * 100}, settings.SECRET_KEY, "HS256"),
        ]
        for claims, key, algorithm in cases:
            with self.subTest(claims=claims, algorithm=algorithm):
                token = jwt.encode(claims, key, algorithm=algorithm)
                User.objects.filter(pk=self.user.pk).update(Token=token)
                self.assertEqual(self.client.get("/auth", HTTP_AUTHORIZATION="Bearer " + token).status_code, 401)
