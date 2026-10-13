from django.urls import path

from . import views

urlpatterns = [
    path('professores/', views.professores, name='professores'),
    path('login/', views.login, name='login'),

    path('materias/', views.materias, name='materias'),
    path('materias/<int:materia_id>/', views.materias, name='materia-detalhe'),

    path('turmas/', views.turmas, name='turmas'),
    path('turmas/<int:turma_id>/', views.turmas, name='turma-detalhe'),

    path('alunos/', views.alunos, name='alunos'),
    path('alunos/<int:aluno_id>/', views.alunos, name='aluno-detalhe'),

    path('questoes/', views.questoes, name='questoes'),
    path('questoes/<int:pk>/', views.questao_detalhe, name='questao-detalhe'),

    path('provas/', views.provas, name='provas'),
    path('provas/<int:pk>/', views.prova_detalhe, name='prova-detalhe'),
    path('provas/<int:pk>/versoes/', views.gerar_versoes, name='prova-gerar-versoes'),
    path('provas/<int:pk>/aplicar/', views.aplicar_prova, name='prova-aplicar'),

    path('versoes/<int:pk>/', views.versao_detalhe, name='versao-detalhe'),
    path('versoes/<int:pk>/completa/', views.versao_completa, name='versao-completa'),

    path('avaliacoes/', views.avaliacoes, name='avaliacoes'),
]
