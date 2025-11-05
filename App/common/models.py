from django.db import models
from django.db import models
from django.conf import settings
from django.utils.timezone import now

class Notification(models.Model):
    KIND_CHOICES = (
        ("review_request","Solicitud de calificación"),
        ("generic","Genérica"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=32, choices=KIND_CHOICES, default="generic")
    title = models.CharField(max_length=140)
    body = models.TextField(blank=True)
    action_url = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def active(self):
        if self.read_at:
            return False
        return not (self.expires_at and now() > self.expires_at)
