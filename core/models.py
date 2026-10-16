from django.db import models


class Professor(models.Model):
    nome = models.TextField(null=True, blank=True)
    email = models.TextField(null=True, blank=True, unique=True)
    senha = models.CharField(max_length=255, null=True, blank=True)  # guarda o HASH, nunca a senha pura
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'professor'
        managed = False

    def to_dict(self):
        return {'id': self.id, 'nome': self.nome, 'email': self.email, 'ativo': self.ativo}


class Materia(models.Model):
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, db_column='professor_id',related_name='materias', null=True)
    nome = models.CharField(max_length=255, null=True, blank=True)
    descricao = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'materia'
        managed = False

    def to_dict(self):
        return {
            'id': self.id, 'professor_id': self.professor_id, 'nome': self.nome,
            'descricao': self.descricao,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Turma(models.Model):
    professor = models.ForeignKey(Professor, on_delete=models.SET_NULL, db_column='professor_id', related_name='turmas', null=True, blank=True)
    ano = models.PositiveSmallIntegerField()
    disciplina = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'turma'
        managed = False
        ordering = ('ano', 'disciplina')

    def __str__(self):
        return f'{self.ano}º ano - {self.disciplina}'


class Aluno(models.Model):
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, db_column='turma_id', related_name='alunos')
    nome = models.CharField(max_length=150)
    ra = models.CharField(max_length=30)
    email = models.EmailField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'aluno'
        managed = False
        ordering = ('nome',)

    def __str__(self):
        return self.nome

class Questao(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, db_column='materia_id', related_name='questoes',null=True)
    enunciado = models.TextField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'questao'
        managed = False

    def to_dict(self):
        return {
            'id': self.id, 'materia_id': self.materia_id, 'enunciado': self.enunciado, 'ativo': self.ativo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'alts': [a.to_dict() for a in self.alternativas.order_by('ordem_original')],
        }


class Alternativa(models.Model):
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE, db_column='questao_id',related_name='alternativas', null=True)
    texto = models.TextField(null=True, blank=True)
    ordem_original = models.IntegerField(null=True, blank=True)
    correta = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'alternativa'
        managed = False
        ordering = ['ordem_original']

    def to_dict(self):
        return {
            'id': self.id, 'questao_id': self.questao_id, 'texto': self.texto,
            'ordem_original': self.ordem_original, 'correta': self.correta,
        }


class Prova(models.Model):
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, db_column='professor_id',related_name='provas', null=True)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, db_column='materia_id', related_name='provas',null=True)
    nome = models.CharField(max_length=255, null=True, blank=True)
    descricao = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'prova'
        managed = False

    def to_dict(self):
        versoes = list(self.versoes.order_by('id'))
        n_questoes = versoes[-1].itens.count() if versoes else 0
        return {
            'id': self.id, 'professor_id': self.professor_id, 'materia_id': self.materia_id,
            'nome': self.nome, 'descricao': self.descricao, 'n_questoes': n_questoes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'versoes': [{'id': v.id, 'codigo': v.codigo, 'uuid': str(v.uuid)} for v in versoes],
        }


class VersaoProva(models.Model):
    prova = models.ForeignKey(Prova, on_delete=models.CASCADE, db_column='prova_id', related_name='versoes',null=True)
    uuid = models.UUIDField()
    codigo = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'versao_prova'
        managed = False

    def to_dict(self):
        itens = list(self.itens.order_by('ordem'))
        gabarito_por_pq = {g.prova_questao_id: g.alternativa_id for g in Gabarito.objects.filter(versao_prova=self)}
        return {
            'id': self.id, 'prova_id': self.prova_id, 'uuid': str(self.uuid), 'codigo': self.codigo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'itens': [it.to_dict(gabarito_por_pq.get(it.id)) for it in itens],
        }


class ProvaQuestao(models.Model):
    versao_prova = models.ForeignKey(VersaoProva, on_delete=models.CASCADE, db_column='versao_prova_id',related_name='itens', null=True)
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE, db_column='questao_id', null=True)
    ordem = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'prova_questao'
        managed = False
        ordering = ['ordem']

    def to_dict(self, alternativa_correta_id=None):
        return {
            'id': self.id, 'versao_prova_id': self.versao_prova_id, 'questao_id': self.questao_id,
            'ordem': self.ordem, 'alternativa_correta_id': alternativa_correta_id,
        }


class Gabarito(models.Model):
    versao_prova = models.ForeignKey(VersaoProva, on_delete=models.CASCADE, db_column='versao_prova_id', null=True)
    prova_questao = models.ForeignKey(ProvaQuestao, on_delete=models.CASCADE, db_column='prova_questao_id',
                                       null=True)
    alternativa = models.ForeignKey(Alternativa, on_delete=models.CASCADE, db_column='alternativa_id', null=True)

    class Meta:
        db_table = 'gabarito'
        managed = False


class Avaliacao(models.Model):
    versao_prova = models.ForeignKey(VersaoProva, on_delete=models.CASCADE, db_column='versao_prova_id',related_name='avaliacoes', null=True)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, db_column='aluno_id', related_name='avaliacoes',null=True)
    data_aplicacao = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True, default='aplicada')
    nota = models.FloatField(null=True, blank=True)
    data_correcao = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'avaliacao'
        managed = False

    def to_dict(self, com_respostas=True):
        v= self.versao_prova
        prova = v.prova if v else None
        aluno = self.aluno
        turma = aluno.turma if aluno else None
        d = {
            'id': self.id, 'versao_prova_id': self.versao_prova_id, 'aluno_id': self.aluno_id,
            'data_aplicacao': self.data_aplicacao.isoformat() if self.data_aplicacao else None,
            'status': self.status, 'nota': self.nota,
            'data_correcao': self.data_correcao.isoformat() if self.data_correcao else None,
            'aluno_nome': aluno.nome if aluno else '', 'aluno_ra': aluno.ra if aluno else '',
            'turma_id': turma.id if turma else None, 'turma_nome': str(turma) if turma else '',
            'prova_id': prova.id if prova else None, 'prova_nome': prova.nome if prova else '',
            'versao_codigo': v.codigo if v else '', 'versao_uuid': str(v.uuid) if v else None,
        }
        if com_respostas:
            d['respostas'] = [r.to_dict() for r in self.respostas.all()]
        return d


class Resposta(models.Model):
    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.CASCADE, db_column='avaliacao_id',related_name='respostas', null=True)
    prova_questao = models.ForeignKey(ProvaQuestao, on_delete=models.CASCADE, db_column='prova_questao_id',null=True)
    alternativa = models.ForeignKey(Alternativa, on_delete=models.SET_NULL, db_column='alternativa_id', null=True,blank=True)
    correta = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'resposta'
        managed = False

    def to_dict(self):
        return {
            'id': self.id, 'avaliacao_id': self.avaliacao_id, 'prova_questao_id': self.prova_questao_id,
            'alternativa_id': self.alternativa_id, 'correta': self.correta,
        }
