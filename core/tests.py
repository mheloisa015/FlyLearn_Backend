import json

from django.test import TestCase

from .models import Aluno, Turma


class ApiTurmaAlunoTests(TestCase):
    def post(self, url, data):
        return self.client.post(url, json.dumps(data), content_type='application/json')

    def put(self, url, data):
        return self.client.put(url, json.dumps(data), content_type='application/json')

    def test_crud_turma(self):
        r = self.post('/turmas/', {'ano': 3, 'disciplina': 'Matemática'})
        self.assertEqual(r.status_code, 201)
        tid = r.json()['id']
        self.assertEqual(self.client.get('/turmas/').json()[0]['total_alunos'], 0)
        r = self.put(f'/turmas/{tid}/', {'ano': 4, 'disciplina': 'Matemática'})
        self.assertEqual(r.json()['ano'], 4)
        self.assertEqual(self.client.delete(f'/turmas/{tid}/').status_code, 204)

    def test_turma_validacoes(self):
        self.assertEqual(self.post('/turmas/', {'ano': 13, 'disciplina': 'X'}).status_code, 400)
        self.assertEqual(self.post('/turmas/', {'ano': 3, 'disciplina': ' '}).status_code, 400)
        self.post('/turmas/', {'ano': 3, 'disciplina': 'Matemática'})
        self.assertEqual(self.post('/turmas/', {'ano': 3, 'disciplina': 'matemática'}).status_code, 409)

    def test_crud_aluno_e_regras(self):
        t = Turma.objects.create(ano=3, disciplina='Matemática')
        r = self.post('/alunos/', {'turma_id': t.id, 'nome': 'Ana', 'ra': 20240117, 'email': 'ana@escola.com'})
        self.assertEqual(r.status_code, 201)
        aid = r.json()['id']
        # RA duplicado
        self.assertEqual(self.post('/alunos/', {'turma_id': t.id, 'nome': 'B', 'ra': 20240117}).status_code, 409)
        # e-mail inválido / turma inexistente / RA inválido
        self.assertEqual(self.post('/alunos/', {'turma_id': t.id, 'nome': 'B', 'ra': 1, 'email': 'x'}).status_code, 400)
        self.assertEqual(self.post('/alunos/', {'turma_id': 999, 'nome': 'B', 'ra': 2}).status_code, 400)
        self.assertEqual(self.post('/alunos/', {'turma_id': t.id, 'nome': 'B', 'ra': 'abc'}).status_code, 400)
        # turma com aluno não pode ser excluída
        self.assertEqual(self.client.delete(f'/turmas/{t.id}/').status_code, 409)
        # filtros
        self.assertEqual(len(self.client.get(f'/alunos/?turma_id={t.id}').json()), 1)
        self.assertEqual(len(self.client.get('/alunos/?q=an').json()), 1)
        self.assertEqual(len(self.client.get('/alunos/?q=2024').json()), 1)
        self.assertEqual(len(self.client.get('/alunos/?q=zzz').json()), 0)
        # edição parcial e exclusão
        r = self.client.patch(f'/alunos/{aid}/', json.dumps({'nome': 'Ana B'}), content_type='application/json')
        self.assertEqual(r.json()['nome'], 'Ana B')
        self.assertEqual(self.client.delete(f'/alunos/{aid}/').status_code, 204)
        self.assertEqual(Aluno.objects.count(), 0)

    def test_json_invalido(self):
        r = self.client.post('/turmas/', 'não é json', content_type='application/json')
        self.assertEqual(r.status_code, 400)
