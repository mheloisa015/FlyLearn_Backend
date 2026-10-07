from django.db import models


class Turma(models.Model):
    """Turma de um professor: ano + disciplina."""
    professor_id = models.PositiveIntegerField(default=1)  # virá da sessão/auth quando houver login
    ano = models.PositiveSmallIntegerField()
    disciplina = models.CharField(max_length=100)

    class Meta:
        ordering = ['ano', 'disciplina']

    def __str__(self):
        return f'{self.ano}º ano · {self.disciplina}'

    def to_dict(self):
        return {
            'id': self.id,
            'professor_id': self.professor_id,
            'ano': self.ano,
            'disciplina': self.disciplina,
            'total_alunos': self.alunos.count(),
        }


class Aluno(models.Model):
    """Aluno pertence a uma turma."""
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT, related_name='alunos')
    nome = models.CharField(max_length=150)
    ra = models.PositiveBigIntegerField(unique=True)
    email = models.EmailField(blank=True, default='')

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.ra})'

    def to_dict(self):
        return {
            'id': self.id,
            'turma_id': self.turma_id,
            'turma': str(self.turma),
            'nome': self.nome,
            'ra': self.ra,
            'email': self.email,
        }
