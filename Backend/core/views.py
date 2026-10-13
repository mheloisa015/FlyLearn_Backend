import json

from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Aluno, Materia, Turma


def turma_json(turma):
	return {'id': turma.id, 'ano': turma.ano, 'disciplina': turma.disciplina}


def aluno_json(aluno):
	return {'id': aluno.id, 'turma_id': aluno.turma_id, 'nome': aluno.nome, 'ra': aluno.ra, 'email': aluno.email}


def materia_json(materia):
	return {
		'id': materia.id,
		'nome': materia.nome,
		'descricao': materia.descricao,
		'created_at': materia.created_at.isoformat(),
		'updated_at': materia.updated_at.isoformat(),
	}


def resposta(request, data, status=200):
	response = JsonResponse(data, status=status)
	response['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
	response['Access-Control-Allow-Headers'] = 'Content-Type'
	response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
	return response


def dados(request):
	return json.loads(request.body or '{}')


@csrf_exempt
@require_http_methods(['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def turmas(request, turma_id=None):
	if request.method == 'OPTIONS':
		return resposta(request, {})
	if request.method == 'GET':
		return resposta(request, {'turmas': [turma_json(t) for t in Turma.objects.all()], 'alunos': [aluno_json(a) for a in Aluno.objects.all()]})
	if request.method == 'POST':
		try:
			body = dados(request)
			ano = int(body.get('ano', 0))
			disciplina = str(body.get('disciplina', '')).strip()
			if not 1 <= ano <= 12 or not disciplina:
				return resposta(request, {'error': 'Ano e disciplina são obrigatórios.'}, 400)
			turma = Turma.objects.create(ano=ano, disciplina=disciplina)
		except (ValueError, TypeError, json.JSONDecodeError, IntegrityError):
			return resposta(request, {'error': 'Essa turma já está cadastrada ou possui dados inválidos.'}, 400)
		return resposta(request, turma_json(turma), 201)
	try:
		turma = Turma.objects.get(pk=turma_id)
	except Turma.DoesNotExist:
		return resposta(request, {'error': 'Turma não encontrada.'}, 404)
	if request.method == 'DELETE':
		turma.delete()
		return resposta(request, {})
	try:
		body = dados(request)
		turma.ano = int(body.get('ano', turma.ano))
		turma.disciplina = str(body.get('disciplina', turma.disciplina)).strip()
		if not 1 <= turma.ano <= 12 or not turma.disciplina:
			return resposta(request, {'error': 'Ano e disciplina são obrigatórios.'}, 400)
		turma.save()
	except (ValueError, TypeError, json.JSONDecodeError, IntegrityError):
		return resposta(request, {'error': 'Essa turma já está cadastrada ou possui dados inválidos.'}, 400)
	return resposta(request, turma_json(turma))


@csrf_exempt
@require_http_methods(['POST', 'PUT', 'DELETE', 'OPTIONS'])
def alunos(request, aluno_id=None):
	if request.method == 'OPTIONS':
		return resposta(request, {})
	if request.method == 'POST':
		try:
			body = dados(request)
			turma = Turma.objects.get(pk=int(body.get('turma_id', 0)))
			nome = str(body.get('nome', '')).strip()
			ra = str(body.get('ra', '')).strip()
			if not nome or not ra:
				return resposta(request, {'error': 'Nome e RA são obrigatórios.'}, 400)
			aluno = Aluno.objects.create(turma=turma, nome=nome, ra=ra, email=str(body.get('email', '')).strip())
		except (ValueError, TypeError, json.JSONDecodeError, Turma.DoesNotExist, IntegrityError):
			return resposta(request, {'error': 'Aluno inválido ou RA já cadastrado nesta turma.'}, 400)
		return resposta(request, aluno_json(aluno), 201)
	try:
		aluno = Aluno.objects.get(pk=aluno_id)
	except Aluno.DoesNotExist:
		return resposta(request, {'error': 'Aluno não encontrado.'}, 404)
	if request.method == 'DELETE':
		aluno.delete()
		return resposta(request, {})
	try:
		body = dados(request)
		aluno.turma_id = int(body.get('turma_id', aluno.turma_id))
		aluno.nome = str(body.get('nome', aluno.nome)).strip()
		aluno.ra = str(body.get('ra', aluno.ra)).strip()
		aluno.email = str(body.get('email', aluno.email)).strip()
		aluno.save()
	except (ValueError, TypeError, json.JSONDecodeError, IntegrityError):
		return resposta(request, {'error': 'Aluno inválido ou RA já cadastrado nesta turma.'}, 400)
	return resposta(request, aluno_json(aluno))


@csrf_exempt
@require_http_methods(['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def materias(request, materia_id=None):
	if request.method == 'OPTIONS':
		return resposta(request, {})
	if request.method == 'GET':
		return resposta(request, {'materias': [materia_json(m) for m in Materia.objects.all()]})
	if request.method == 'POST':
		try:
			body = dados(request)
			nome = str(body.get('nome', '')).strip()
			if not nome:
				return resposta(request, {'error': 'Nome da matéria é obrigatório.'}, 400)
			materia = Materia.objects.create(nome=nome, descricao=str(body.get('descricao', '')).strip())
		except (ValueError, TypeError, json.JSONDecodeError, IntegrityError):
			return resposta(request, {'error': 'Essa matéria já está cadastrada ou possui dados inválidos.'}, 400)
		return resposta(request, materia_json(materia), 201)
	try:
		materia = Materia.objects.get(pk=materia_id)
	except Materia.DoesNotExist:
		return resposta(request, {'error': 'Matéria não encontrada.'}, 404)
	if request.method == 'DELETE':
		materia.delete()
		return resposta(request, {})
	try:
		body = dados(request)
		materia.nome = str(body.get('nome', materia.nome)).strip()
		materia.descricao = str(body.get('descricao', materia.descricao)).strip()
		if not materia.nome:
			return resposta(request, {'error': 'Nome da matéria é obrigatório.'}, 400)
		materia.save()
	except (ValueError, TypeError, json.JSONDecodeError, IntegrityError):
		return resposta(request, {'error': 'Essa matéria já está cadastrada ou possui dados inválidos.'}, 400)
	return resposta(request, materia_json(materia))
