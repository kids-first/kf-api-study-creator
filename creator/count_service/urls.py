from django.urls import path, include
import creator.count_service.views


urlpatterns = [
    path(
        r"status",
        creator.count_service.views.status,
    ),
    path(
        r"tasks",
        creator.count_service.views.tasks,
    ),
]
