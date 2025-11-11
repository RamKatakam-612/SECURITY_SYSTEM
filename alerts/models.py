from django.db import models

class Alert(models.Model):
    track_id = models.IntegerField()
    duration = models.FloatField()
    image = models.ImageField(upload_to="alerts/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Track {self.track_id} | {self.duration:.1f}s"
