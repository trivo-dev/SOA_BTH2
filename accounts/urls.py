from django.urls import path
from . import views

urlpatterns = [
    path("", views.login, name="login"),
    path("auth", views.auth, name="auth"),
    path("hello", views.hello, name="hello"),
]
