from django.db import models


class Materia(models.Model):
	nome = models.CharField(max_length=100)
	descricao = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ('nome',)
		constraints = [
			models.UniqueConstraint(fields=('nome',), name='unique_materia_nome'),
		]

	def __str__(self):
		return self.nome


class Turma(models.Model):
	ano = models.PositiveSmallIntegerField()
	disciplina = models.CharField(max_length=100)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ('ano', 'disciplina')
		constraints = [
			models.UniqueConstraint(fields=('ano', 'disciplina'), name='unique_turma_ano_disciplina'),
		]

	def __str__(self):
		return f'{self.ano}º ano - {self.disciplina}'


class Aluno(models.Model):
	turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='alunos')
	nome = models.CharField(max_length=150)
	ra = models.CharField(max_length=30)
	email = models.EmailField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ('nome',)
		constraints = [
			models.UniqueConstraint(fields=('turma', 'ra'), name='unique_aluno_ra_turma'),
		]

	def __str__(self):
		return self.nome
