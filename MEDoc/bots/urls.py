from django.urls import path
from . import views


urlpatterns = [
    path('vk_bot', views.index_vk)
]
