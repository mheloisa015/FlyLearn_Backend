from django.urls import path

from . import views

urlpatterns = [
    path('turmas/', views.turmas, name='turmas'),
    path('turmas/<int:pk>/', views.turma_detalhe, name='turma_detalhe'),
    path('alunos/', views.alunos, name='alunos'),
    path('alunos/<int:pk>/', views.aluno_detalhe, name='aluno_detalhe'),
]
