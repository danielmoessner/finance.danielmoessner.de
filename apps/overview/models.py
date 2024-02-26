from django.db import models

from apps.users.models import StandardUser


class Bucket(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(StandardUser, on_delete=models.CASCADE, related_name="buckets")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_amount(self):
        return 0
    
    def get_percentage(self):
        return 0
