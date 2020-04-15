from django.urls import path
from . import views

urlpatterns = [
    path("reset-db/", views.reset_db, name="reset_db"),
    path("change-groups/", views.change_groups, name="change_groups"),
]
