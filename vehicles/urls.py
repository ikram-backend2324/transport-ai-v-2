from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('inspections/', views.index, name='index'),
    path('upload/', views.upload, name='upload'),
    path('result/<int:pk>/', views.result, name='result'),
]
