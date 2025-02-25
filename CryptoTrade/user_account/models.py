from django.db import models
from django.utils import timezone

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=200, null = True, blank = True)
    email = models.EmailField(max_length=200, null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True, default=timezone.now)
    password = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name

