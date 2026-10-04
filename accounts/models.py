from django.db import models


class User(models.Model):
    IdUser = models.AutoField(primary_key=True)
    UserName = models.CharField(max_length=255, unique=True)
    Password = models.CharField(max_length=255)
    Token = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "User"
