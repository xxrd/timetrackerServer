from django.urls import include, path
from . import views

urlpatterns = [
    path('users/', include('users.urls')),
    path('rest-auth/', include('rest_auth.urls')),
    path('rest-auth/registration/', include('rest_auth.registration.urls')),
    path('tasks', views.APITasks.as_view()),
	path('tasks/<int:pk>', views.APITasksDetail.as_view()),
]
