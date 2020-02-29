from django.db import models
import datetime
from users.models import CustomUser
from django.utils import timezone

class Task(models.Model):
	title = models.TextField()
	executor = models.TextField(null=True, blank=True)
	startDateTime = models.DateTimeField(auto_now_add=True, db_index=True)
	endDateTime = models.DateTimeField(null=True, blank=True)
	status = models.CharField(max_length=64)
	timerTimeFromLastPause = models.DurationField(null=True, blank=True)
	lastStartDateTime = models.DateTimeField(auto_now_add=True)
	timerStatus = models.CharField(max_length=64)
	user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
	
	@property
	def timerTime(self):
		if self.timerStatus == self.TimerStatus.run:
			if self.timerTimeFromLastPause != None:
				d = (self.timerTimeFromLastPause + (timezone.now() - self.lastStartDateTime))
				return d
			else:
				d = (timezone.now() - self.lastStartDateTime)
				return d
		elif self.timerStatus == self.TimerStatus.stop:
			d = self.timerTimeFromLastPause
			return d
		return None

	class Meta:
		ordering = ['timerStatus']

	class TaskStatus:
		active = "active"
		complete = "complete"

	class TimerStatus:
		run = "run"
		stop = "stop"

