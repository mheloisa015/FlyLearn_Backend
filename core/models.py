from django.db import models


class Professor(models.Model):
    """Mapeia a tabela `professor` que já existe no Postgres (criada pelo pgAdmin).
    managed=False: o Django NÃO cria/altera essa tabela, só lê e grava nela."""
    nome = models.TextField()
    email = models.TextField(unique=True)
    senha = models.CharField(max_length=255)  # guarda o HASH, nunca a senha pura
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'professor'
        managed = False

    def to_dict(self):
        return {'id': self.id, 'nome': self.nome, 'email': self.email, 'ativo': self.ativo}
