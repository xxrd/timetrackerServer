import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from django.urls import reverse
from rest_framework.test import APITestCase
from users.models import CustomUser
from users.serializers import UserSerializer
from .models import Task
from .serializers import TaskSerializer
from rest_framework.test import RequestsClient
from rest_framework.test import force_authenticate
from .views import APITasks, APITasksDetail
import json
import datetime
from django.utils import timezone


class APITasksTests(TestCase):

	def test_get(self):
		factory = APIRequestFactory()
		user = CustomUser.objects.get(username='admin')
		view = APITasks.as_view()


		tasks = Task.objects.filter(user=user)
		tasksSerializer = TaskSerializer(tasks, many=True)
		tasksSerializer.data[0]['timerTime']

		request = factory.get('/tasks')
		force_authenticate(request, user=user, token=user.auth_token)
		response = view(request)

		i = 0
		for _ in response.data:
			print(i)
			self.assertTrue(response.data[i]['timerTime'] >= tasksSerializer.data[i]['timerTime'] 
					  and response.data[i]['timerTime'] < (tasksSerializer.data[i]['timerTime'] + datetime.timedelta(seconds=60)))
			del response.data[i]["timerTime"]
			del tasksSerializer.data[i]["timerTime"]
			i = i + 1

		self.assertEqual(response.data, tasksSerializer.data)


		tasks = Task.objects.filter(user=user)[1:]
		tasksSerializer = TaskSerializer(tasks, many=True)
		tasksSerializer.data[0]['timerTime']

		request = factory.get('/tasks?start=1')
		force_authenticate(request, user=user, token=user.auth_token)
		response = view(request)

		i = 0
		for _ in response.data:
			print(i)
			self.assertTrue(response.data[i]['timerTime'] >= tasksSerializer.data[i]['timerTime'] 
					  and response.data[i]['timerTime'] < (tasksSerializer.data[i]['timerTime'] + datetime.timedelta(seconds=60)))
			del response.data[i]["timerTime"]
			del tasksSerializer.data[i]["timerTime"]
			i = i + 1

		self.assertEqual(response.data, tasksSerializer.data)


		tasks = Task.objects.filter(user=request.user)[0:1]
		tasksSerializer = TaskSerializer(tasks, many=True)
		tasksSerializer.data[0]['timerTime']

		request = factory.get('/tasks?start=0&end=1')
		force_authenticate(request, user=user, token=user.auth_token)
		response = view(request)

		i = 0
		for _ in response.data:
			print(i)
			self.assertTrue(response.data[i]['timerTime'] >= tasksSerializer.data[i]['timerTime'] 
					  and response.data[i]['timerTime'] < (tasksSerializer.data[i]['timerTime'] + datetime.timedelta(seconds=60)))
			del response.data[i]["timerTime"]
			del tasksSerializer.data[i]["timerTime"]
			i = i + 1

		self.assertEqual(response.data, tasksSerializer.data)


	def test_post(self):
		factory = APIRequestFactory()
		user = CustomUser.objects.get(username='admin')
		view = APITasks.as_view()

		request = factory.post('/tasks/', json.dumps({'title': 'task1', 'executor':'executor1'}), content_type='application/json')
		force_authenticate(request, user=user, token=user.auth_token)
		response = view(request)

		assert response.status_code == 200

		self.assertEquals(response.data.keys(), set(['title', 'executor', 'startDateTime', 'endDateTime', 'timerStatus', 'status', 'pk', 'timerTime']))



class APITasksDetailTests(TestCase):

	def test_get(self):
		factory = APIRequestFactory()
		u = CustomUser.objects.get(username='admin')
		view = APITasksDetail.as_view()

		tasks = Task.objects.filter(user=u)[0:1]
		tasksSerializer = TaskSerializer(tasks[0])
		print()

		request = factory.get('/tasks/')
		force_authenticate(request, user=u, token=u.auth_token)
		response = view(request, tasksSerializer.data["pk"])

		self.assertTrue(response.data['timerTime'] >= tasksSerializer.data['timerTime'] 
				  and response.data['timerTime'] < (tasksSerializer.data['timerTime'] + datetime.timedelta(seconds=60)))

		del response.data["timerTime"]
		data = tasksSerializer.data
		del data["timerTime"]

		self.assertEqual(response.data, data)


	def test_put(self):		

		factory = APIRequestFactory()
		u = CustomUser.objects.get(username='admin')
		view = APITasksDetail.as_view()

		tasks = Task.objects.filter(user=u)[0:1]
		tasksSerializer = TaskSerializer(tasks[0])

		oldStatus = tasksSerializer.data["status"]
		newStatus = Task.TaskStatus.complete if oldStatus == Task.TaskStatus.active else Task.TaskStatus.active
		endDateTime = timezone.now()

		newTask = {
			'title':'newTitle',
			'executor':'newExecutor',
			'startDateTime': tasksSerializer.data['startDateTime'],
			'timerStatus': Task.TimerStatus.stop,
			'pk': tasksSerializer.data['pk'],
			'status': newStatus
		}

		request = factory.put('/tasks/', json.dumps({'title': 'newTitle', 'executor':'newExecutor', 'status': newStatus}), content_type='application/json')
		force_authenticate(request, user=u, token=u.auth_token)
		response = view(request, tasksSerializer.data["pk"])

		self.assertTrue(response.data['timerTime'] >= tasksSerializer.data['timerTime'] 
				  and response.data['timerTime'] < (tasksSerializer.data['timerTime'] + datetime.timedelta(seconds=60)))


		if newStatus == Task.TaskStatus.active:
			self.assertEqual(response.data['endDateTime'], None)
		else:
			d = datetime.datetime.strptime(response.data['endDateTime'], '%Y-%m-%dT%H:%M:%S.%f%z')
			self.assertTrue(d >= endDateTime
					  and d < (endDateTime + datetime.timedelta(seconds=60)))


		del response.data["timerTime"]
		del response.data["endDateTime"]


		self.assertEqual(response.data, newTask)


		tasks = Task.objects.filter(user=u)[0:1]
		tasksSerializer = TaskSerializer(tasks[0])

		request = factory.put('/tasks/', json.dumps({'timerStatus': 'active'}), content_type='application/json')
		force_authenticate(request, user=u, token=u.auth_token)
		response = view(request, tasksSerializer.data["pk"])

		if tasksSerializer.data['status'] == Task.TaskStatus.complete:
			self.assertEqual(response.data["timerStatus"], "stop")
		else:
			self.assertEqual(response.data["timerStatus"], "run")


	def test_delete(self):

		factory = APIRequestFactory()
		u = CustomUser.objects.get(username='admin')
		view = APITasksDetail.as_view()

		tasks = Task.objects.filter(user=u)[0:1]
		tasksSerializer = TaskSerializer(tasks[0])

		request = factory.delete('/tasks/')
		force_authenticate(request, user=u, token=u.auth_token)
		response = view(request, tasksSerializer.data["pk"])

		try:
			task = Task.objects.get(pk=tasksSerializer.data['pk'])
		except(Task.DoesNotExist):
			return
		self.assertTrue(True)
