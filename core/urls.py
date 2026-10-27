from django.urls import path

from . import views

urlpatterns = [
    path('professores/', views.professores, name='professores'),
    path('professores/<int:pk>/', views.professor_detalhe, name='professor-detalhe'),
    path('professores/<int:pk>/senha/', views.professor_senha, name='professor-senha'),
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
    path('versoes/<int:pk>/qr.png', views.versao_qr, name='versao-qr'),
    path('versoes/uuid/<str:uuid>/', views.versao_por_uuid, name='versao-por-uuid'),

    path('avaliacoes/', views.avaliacoes, name='avaliacoes'),
    path('avaliacoes/<int:pk>/', views.avaliacao_detalhe, name='avaliacao-detalhe'),
    path('avaliacoes/<int:pk>/resultado/', views.salvar_resultado, name='avaliacao-resultado'),

    path('recuperar-senha/', views.recuperar_senha, name='recuperar-senha'),
    path('recuperar-senha/validar/', views.validar_token_senha, name='recuperar-senha-validar'),
    path('redefinir-senha/', views.redefinir_senha, name='redefinir-senha'),
]
