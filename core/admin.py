from django.contrib import admin
from .models import Turma, Aluno


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ('ano', 'disciplina', 'professor_id')
    search_fields = ('disciplina',)


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ra', 'email', 'turma')
    list_filter = ('turma',)
    search_fields = ('nome', 'ra', 'email')
