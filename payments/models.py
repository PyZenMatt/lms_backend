from django.db import models


# Record external provider events to ensure idempotent processing.
class PaymentEvent(models.Model):
	provider_event_id = models.CharField(max_length=255, unique=True)
	provider = models.CharField(max_length=64)
	payload = models.JSONField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.provider}:{self.provider_event_id}"
