from django.urls import path
from . import views

urlpatterns = [path("reset-db/", views.reset_db, name="reset_db")]
