from django.urls import path

from . import views

urlpatterns = [
    path('professores/', views.professores, name='professores'),
]