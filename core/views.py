import json

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Aluno, Turma

PROFESSOR_ID = 1  # TODO: trocar por request.user quando existir login


def _erro(msg, status=400, campo=None):
    corpo = {'erro': msg}
    if campo:
        corpo['campo'] = campo
    return JsonResponse(corpo, status=status)


def _body(request):
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _int(valor):
    try:
        if isinstance(valor, bool):
            return None
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ TURMA
def _validar_turma(data, instancia=None):
    ano = _int(data.get('ano'))
    disciplina = str(data.get('disciplina') or '').strip()
    if ano is None or not 1 <= ano <= 12:
        return None, _erro('Informe um ano entre 1 e 12.', campo='ano')
    if not disciplina:
        return None, _erro('Informe a disciplina.', campo='disciplina')
    if len(disciplina) > 100:
        return None, _erro('Disciplina deve ter no máximo 100 caracteres.', campo='disciplina')
    dup = Turma.objects.filter(professor_id=PROFESSOR_ID, ano=ano, disciplina__iexact=disciplina)
    if instancia:
        dup = dup.exclude(pk=instancia.pk)
    if dup.exists():
        return None, _erro('Você já tem essa turma (mesmo ano e disciplina).', 409, 'disciplina')
    return {'ano': ano, 'disciplina': disciplina}, None


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def turmas(request):
    if request.method == 'GET':
        qs = Turma.objects.filter(professor_id=PROFESSOR_ID)
        return JsonResponse([t.to_dict() for t in qs], safe=False)

    data = _body(request)
    if data is None:
        return _erro('JSON inválido.')
    campos, erro = _validar_turma(data)
    if erro:
        return erro
    turma = Turma.objects.create(professor_id=PROFESSOR_ID, **campos)
    return JsonResponse(turma.to_dict(), status=201)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def turma_detalhe(request, pk):
    try:
        turma = Turma.objects.get(pk=pk, professor_id=PROFESSOR_ID)
    except Turma.DoesNotExist:
        return _erro('Turma não encontrada.', 404)

    if request.method == 'GET':
        return JsonResponse(turma.to_dict())

    if request.method == 'DELETE':
        n = turma.alunos.count()
        if n:
            return _erro(f'Não é possível excluir: a turma tem {n} aluno(s).', 409)
        turma.delete()
        return HttpResponse(status=204)

    data = _body(request)
    if data is None:
        return _erro('JSON inválido.')
    data = {'ano': turma.ano, 'disciplina': turma.disciplina, **data}  # PATCH parcial
    campos, erro = _validar_turma(data, turma)
    if erro:
        return erro
    turma.ano, turma.disciplina = campos['ano'], campos['disciplina']
    turma.save()
    return JsonResponse(turma.to_dict())


# ------------------------------------------------------------------ ALUNO
def _validar_aluno(data, instancia=None):
    turma_id = _int(data.get('turma_id'))
    nome = str(data.get('nome') or '').strip()
    ra = _int(data.get('ra'))
    email = str(data.get('email') or '').strip()

    turma = Turma.objects.filter(pk=turma_id, professor_id=PROFESSOR_ID).first() if turma_id else None
    if not turma:
        return None, _erro('Selecione uma turma válida.', campo='turma_id')
    if not nome:
        return None, _erro('Informe o nome completo.', campo='nome')
    if len(nome) > 150:
        return None, _erro('Nome deve ter no máximo 150 caracteres.', campo='nome')
    if ra is None or ra <= 0:
        return None, _erro('Informe o RA (somente números).', campo='ra')
    if email:
        try:
            validate_email(email)
        except ValidationError:
            return None, _erro('E-mail inválido.', campo='email')
    dup = Aluno.objects.filter(ra=ra)
    if instancia:
        dup = dup.exclude(pk=instancia.pk)
    if dup.exists():
        return None, _erro('Já existe um aluno com esse RA.', 409, 'ra')
    return {'turma': turma, 'nome': nome, 'ra': ra, 'email': email}, None


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def alunos(request):
    if request.method == 'GET':
        qs = Aluno.objects.filter(turma__professor_id=PROFESSOR_ID).select_related('turma')
        turma_id = _int(request.GET.get('turma_id'))
        if turma_id:
            qs = qs.filter(turma_id=turma_id)
        q = request.GET.get('q', '').strip()
        if q:
            from django.db.models import Q
            filtro = Q(nome__icontains=q)
            if q.isdigit():
                filtro |= Q(ra__icontains=q)
            qs = qs.filter(filtro)
        return JsonResponse([a.to_dict() for a in qs], safe=False)

    data = _body(request)
    if data is None:
        return _erro('JSON inválido.')
    campos, erro = _validar_aluno(data)
    if erro:
        return erro
    aluno = Aluno.objects.create(**campos)
    return JsonResponse(aluno.to_dict(), status=201)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def aluno_detalhe(request, pk):
    try:
        aluno = Aluno.objects.select_related('turma').get(pk=pk, turma__professor_id=PROFESSOR_ID)
    except Aluno.DoesNotExist:
        return _erro('Aluno não encontrado.', 404)

    if request.method == 'GET':
        return JsonResponse(aluno.to_dict())

    if request.method == 'DELETE':
        aluno.delete()
        return HttpResponse(status=204)

    data = _body(request)
    if data is None:
        return _erro('JSON inválido.')
    data = {'turma_id': aluno.turma_id, 'nome': aluno.nome, 'ra': aluno.ra,
            'email': aluno.email, **data}  # PATCH parcial
    campos, erro = _validar_aluno(data, aluno)
    if erro:
        return erro
    for k, v in campos.items():
        setattr(aluno, k, v)
    aluno.save()
    return JsonResponse(aluno.to_dict())
