from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import CustomUser
from users.serializers import UserSerializer
from .models import Task
from .serializers import TaskSerializer
from rest_framework import status
from django.utils import timezone
from rest_framework.views import APIView


@permission_classes((IsAuthenticated,))
class APITasks(APIView):

	def get(self, request):
		start = None
		end = None
		if "start" in request.query_params:
			start = request.query_params['start']
			if not start.isdigit():
				return Response({"detail":"start parameter is not valid"}, status=status.HTTP_400_BAD_REQUEST)
			start = int(start)

		if "end" in request.query_params:
			end = request.query_params['end']
			if not end.isdigit():
				return Response({"detail":"end parameter is not valid"}, status=status.HTTP_400_BAD_REQUEST)
			end = int(end)

		if not start is None and not end is None:
			tasks = Task.objects.filter(user=request.user)[start:end]
		elif not start is None:
			tasks = Task.objects.filter(user=request.user)[start:]
		else:
			tasks = Task.objects.filter(user=request.user)

		tasksSerializer = TaskSerializer(tasks, many=True)
		return Response(tasksSerializer.data)

	def post(self, request):
		if not "title" in request.data:
			return Response({"detail":"title required"}, status=status.HTTP_400_BAD_REQUEST)
		if not "executor" in request.data:
			return Response({"detail":"executor required"}, status=status.HTTP_400_BAD_REQUEST)
		if len(request.data) != 2:
			return Response({"detail":"only 2 fields are needed"}, status=status.HTTP_400_BAD_REQUEST)

		task = Task.objects.create(
			title=request.data["title"], 				  
			executor=request.data["executor"],
			status=Task.TaskStatus.active,
			timerStatus=Task.TimerStatus.run,
			user=request.user)

		taskSerializer = TaskSerializer(task)
		return Response(taskSerializer.data)


@permission_classes((IsAuthenticated,))
class APITasksDetail(APIView):

	def get(self, request, pk):
		try:
			task = Task.objects.get(pk=pk)
		except(Task.DoesNotExist):
			return Response({"detail":"task not exists"}, status=status.HTTP_400_BAD_REQUEST)
		if task.user != request.user:
			return Response({"detail":"no access rights"}, status=status.HTTP_403_FORBIDDEN)

		serializer = TaskSerializer(task)
		return Response(serializer.data)

	def put(self, request, pk):
		try:
			task = Task.objects.get(pk=pk)
		except(Task.DoesNotExist):
			return Response({"detail":"task not exists"}, status=status.HTTP_400_BAD_REQUEST)
		if task.user != request.user:
			return Response({"detail":"no access rights"}, status=status.HTTP_403_FORBIDDEN)

		if "status" in request.data and "timerStatus" in request.data:
			return Response({"detail":"You cannot set task status and timer status at the same time"}, status=status.HTTP_400_BAD_REQUEST)
		if "title" in request.data:
			task.title = request.data['title']
		if "executor" in request.data:
			task.executor = request.data['executor']
		if "status" in request.data:
			if request.data['status'] ==  Task.TaskStatus.complete:
				if task.status != Task.TaskStatus.complete:
					task.status = Task.TaskStatus.complete
					task.endDateTime = timezone.now()
					if task.timerStatus == Task.TimerStatus.run:
						task.timerStatus = Task.TimerStatus.stop
						if task.timerTimeFromLastPause is None:
							task.timerTimeFromLastPause = (timezone.now() - task.lastStartDateTime)
						else:
						 task.timerTimeFromLastPause = (timezone.now() - task.lastStartDateTime) + task.timerTimeFromLastPause

			elif request.data['status'] == Task.TaskStatus.active:
				if task.status != Task.TaskStatus.active:
					task.status = Task.TaskStatus.active
					task.endDateTime = None
		elif "timerStatus" in request.data and task.status != Task.TaskStatus.complete:
			if request.data['timerStatus'] == Task.TimerStatus.stop:
				if task.timerStatus != Task.TimerStatus.stop:
					task.timerStatus = Task.TimerStatus.stop
					if task.timerTimeFromLastPause is None:
						task.timerTimeFromLastPause = (timezone.now() - task.lastStartDateTime)
					else:
						task.timerTimeFromLastPause = (timezone.now() - task.lastStartDateTime) + task.timerTimeFromLastPause
			elif request.data['timerStatus'] == Task.TimerStatus.run:
				if task.timerStatus != Task.TimerStatus.run:
					task.timerStatus = Task.TimerStatus.run
					task.lastStartDateTime = timezone.now()
		task.save()
		return Response(TaskSerializer(task).data)

	@permission_classes((IsAuthenticated,))
	def delete(self, request, pk):
		try:
			task = Task.objects.get(pk=pk)
		except(Task.DoesNotExist):
			return Response({"detail":"task not exists"}, status=status.HTTP_400_BAD_REQUEST)
		if task.user != request.user:
			return Response({"detail":"no access rights"}, status=status.HTTP_403_FORBIDDEN)

		task.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)
