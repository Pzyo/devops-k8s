from django.db import models

# Create your models here.

class User(models.Model):
    auth_type = models.CharField(max_length=30)
    token = models.CharField(max_length=100)
    content = models.TextField()
    datetime = models.DateTimeField(auto_now=True)