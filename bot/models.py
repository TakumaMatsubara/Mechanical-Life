from django.db import models

class User(models.Model):
    line_user_id = models.CharField(max_length=255, primary_key=True)
    google_calendar_id = models.CharField(max_length=255)

    def __str__(self):
        return self.line_user_id