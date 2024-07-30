from django.db import models

class User(models.Model):
    user_id = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=255)
    picture_url = models.URLField(null=True, blank=True)
    status_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.display_name
