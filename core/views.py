import json
import random
import uuid as uuid_lib
import datetime as dt

from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.utils import timezone                         
from django.utils.dateparse import parse_date, parse_datetime
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction

from .models import (
    Aluno, Alternativa, Avaliacao, Gabarito, Materia, Prova, ProvaQuestao,
    Professor, Questao, Resposta, Turma, VersaoProva,
)
from .services.qr_generator import build_payload, qr_png_bytes


# monta a resposta de erro que o frontend recebe
def _erro(msg, status=400, campo=None):
    corpo = {'erro': msg}
    if campo:
        corpo['campo'] = campo
    return JsonResponse(corpo, status=status)


# lê o JSON que o frontend enviou
def _body(request):
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _professor_id(request, data=None):
    bruto = (data or {}).get('professor_id') or request.GET.get('professor_id')
    try:
        return int(bruto)
    except (TypeError, ValueError):
        return 1
def _json_erros(view):
    """Se a view quebrar (ex.: coluna inexistente no banco), devolve JSON com o motivo
    em vez de uma página 500 sem informação."""
    import functools, logging

    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            logging.getLogger(__name__).exception('Erro em %s', view.__name__)
            return JsonResponse({'erro': f'Erro interno: {type(exc).__name__}: {exc}'}, status=500)
    return wrapper


def turma_json(turma):
	return {'id': turma.id, 'ano': turma.ano, 'disciplina': turma.disciplina}

def aluno_json(aluno):
	return {'id': aluno.id, 'turma_id': aluno.turma_id, 'nome': aluno.nome, 'ra': aluno.ra, 'email': aluno.email}

def materia_json(materia):
	return {
		'id': materia.id,
		'professor_id': materia.professor_id,
		'nome': materia.nome,
		'descricao': materia.descricao,
		'created_at': materia.created_at.isoformat() if materia.created_at else None,
		'updated_at': materia.updated_at.isoformat() if materia.updated_at else None,
	}

def resposta(request, data, status=200):
	response = JsonResponse(data, status=status, safe=False)
	response['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
	response['Access-Control-Allow-Headers'] = 'Content-Type'
	response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
	return response

def dados(request):
	return json.loads(request.body or '{}')

# CADASTRO PROFESSOR
@csrf_exempt
@require_http_methods(['POST'])
def professores(request):
    data = _body(request)
    if data is None:
        return _erro('Informações inválidas.')
    nome = str(data.get('nome') or '').strip()
    email = str(data.get('email') or '').strip().lower()
    senha = str(data.get('senha') or '')

    if not nome:
        return _erro('Por favor! Insira o nome completo!', campo='nome')
    try:
        validate_email(email)
    except ValidationError:
        return _erro('E-mail inválido.', campo='email')
    if len(senha) < 6:
        return _erro('A senha deve ter pelo menos 6 caracteres!', campo='senha')
    if Professor.objects.filter(email__iexact=email).exists():
        return _erro('Já existe uma conta com esse e-mail.', 409, 'email')

    prof = Professor.objects.create(nome=nome, email=email, senha=make_password(senha))
    return JsonResponse(prof.to_dict(), status=201)


# LOGIN
@csrf_exempt
@require_http_methods(['POST'])
def login(request):
    data = _body(request)
    if data is None:
        return _erro('Informações inválidas.')
    email = str(data.get('email') or '').strip().lower()
    senha = str(data.get('senha') or '')

    if not email or not senha:
        return _erro('Informe o e-mail e a senha!')

    prof = Professor.objects.filter(email__iexact=email).first()
    if not prof or not check_password(senha, prof.senha):
        return _erro('E-mail ou senha incorretos.', 401)
    if not prof.ativo:
        return _erro('Esta conta está desativada.', 403)
    return JsonResponse(prof.to_dict())

#TURMAS
@csrf_exempt
@require_http_methods(['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@_json_erros
def turmas(request, turma_id=None):
	if request.method == 'OPTIONS':
		return resposta(request, {})
	if request.method == 'GET':
		ts, als = Turma.objects.all(), Aluno.objects.all()
		pid = request.GET.get('professor_id')
		if pid and pid.isdigit():
			ts, als = ts.filter(professor_id=pid), als.filter(turma__professor_id=pid)
		return resposta(request, {'turmas': [turma_json(t) for t in ts], 'alunos': [aluno_json(a) for a in als]})
	if request.method == 'POST':
		try:
			body = dados(request)
			ano = int(body.get('ano', 0))
			disciplina = str(body.get('disciplina', '')).strip()
			if not 1 <= ano <= 12 or not disciplina:
				return resposta(request, {'erro': 'Ano e disciplina são obrigatórios.'}, 400)
			pid = body.get('professor_id')
			prof_id = int(pid) if str(pid).isdigit() and Professor.objects.filter(pk=int(pid)).exists() else None
			turma = Turma.objects.create(professor_id=prof_id, ano=ano, disciplina=disciplina)
		except (ValueError, TypeError, json.JSONDecodeError, IntegrityError):
			return resposta(request, {'erro': 'Essa turma já está cadastrada ou possui dados inválidos.'}, 400)
		return resposta(request, turma_json(turma), 201)
	try:
		turma = Turma.objects.get(pk=turma_id)
	except Turma.DoesNotExist:
		return resposta(request, {'erro': 'Turma não encontrada.'}, 404)
	if request.method == 'DELETE':
		turma.delete()
		return resposta(request, {})
	try:
		body = dados(request)
		turma.ano = int(body.get('ano', turma.ano))
		turma.disciplina = str(body.get('disciplina', turma.disciplina)).strip()
		if not 1 <= turma.ano <= 12 or not turma.disciplina:
			return resposta(request, {'erro': 'Ano e disciplina são obrigatórios.'}, 400)
		turma.save()
	except (ValueError, TypeError, json.JSONDecodeError, IntegrityError):
		return resposta(request, {'erro': 'Essa turma já está cadastrada ou possui dados inválidos.'}, 400)
	return resposta(request, turma_json(turma))

#ALUNOS
@csrf_exempt
@require_http_methods(['POST', 'PUT', 'DELETE', 'OPTIONS'])
@_json_erros
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
				return resposta(request, {'erro': 'Nome e RA são obrigatórios.'}, 400)
			aluno = Aluno.objects.create(turma=turma, nome=nome, ra=ra, email=str(body.get('email', '')).strip())
		except (ValueError, TypeError, json.JSONDecodeError, Turma.DoesNotExist, IntegrityError):
			return resposta(request, {'erro': 'Aluno inválido ou RA já cadastrado nesta turma.'}, 400)
		return resposta(request, aluno_json(aluno), 201)
	try:
		aluno = Aluno.objects.get(pk=aluno_id)
	except Aluno.DoesNotExist:
		return resposta(request, {'erro': 'Aluno não encontrado.'}, 404)
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
		return resposta(request, {'erro': 'Aluno inválido ou RA já cadastrado nesta turma.'}, 400)
	return resposta(request, aluno_json(aluno))

#MATERIAS
@csrf_exempt
@require_http_methods(['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@_json_erros
def materias(request, materia_id=None):
	if request.method == 'OPTIONS':
		return resposta(request, {})
	if request.method == 'GET':
		qs = Materia.objects.all().order_by('nome')
		pid = request.GET.get('professor_id')
		if pid and pid.isdigit():
			qs = qs.filter(professor_id=pid)
		return resposta(request, [materia_json(m) for m in qs])
	if request.method == 'POST':
		try:
			body = dados(request)
			nome = str(body.get('nome', '')).strip()
			if not nome:
				return resposta(request, {'erro': 'Nome da matéria é obrigatório.'}, 400)
			pid = body.get('professor_id')
			prof_id = int(pid) if str(pid).isdigit() and Professor.objects.filter(pk=int(pid)).exists() else None
			materia = Materia.objects.create(professor_id=prof_id, nome=nome, descricao=str(body.get('descricao', '')).strip())
		except (ValueError, TypeError, json.JSONDecodeError, IntegrityError):
			return resposta(request, {'erro': 'Essa matéria já está cadastrada ou possui dados inválidos.'}, 400)
		return resposta(request, materia_json(materia), 201)
	try:
		materia = Materia.objects.get(pk=materia_id)
	except Materia.DoesNotExist:
		return resposta(request, {'erro': 'Matéria não encontrada.'}, 404)
	if request.method == 'DELETE':
		materia.delete()
		return resposta(request, {})
	try:
		body = dados(request)
		materia.nome = str(body.get('nome', materia.nome)).strip()
		materia.descricao = str(body.get('descricao', materia.descricao)).strip()
		if not materia.nome:
			return resposta(request, {'erro': 'Nome da matéria é obrigatório.'}, 400)
		materia.save()
	except (ValueError, TypeError, json.JSONDecodeError, IntegrityError):
		return resposta(request, {'erro': 'Essa matéria já está cadastrada ou possui dados inválidos.'}, 400)
	return resposta(request, materia_json(materia))


# VALIDAR ALTERANTIVAS
def _validar_alts(alts):
    if not isinstance(alts, list) or len(alts) < 2 or len(alts) > 5:
        return 'Informe de 2 a 5 alternativas.'
    if any(not str(a.get('texto') or '').strip() for a in alts):
        return 'Preencha o texto de todas as alternativas.'
    if not any(a.get('correta') for a in alts):
        return 'Marque a alternativa correta.'
    return None

#QUESTÕES
@csrf_exempt
@require_http_methods(['GET', 'POST'])
def questoes(request):
    if request.method == 'GET':
        qs = Questao.objects.all()
        materia_id = request.GET.get('materia_id')
        ativo = request.GET.get('ativo')
        if materia_id:
            qs = qs.filter(materia_id=materia_id)
        if ativo in ('0', '1'):
            qs = qs.filter(ativo=(ativo == '1'))
        return JsonResponse([q.to_dict() for q in qs.order_by('-id')], safe=False)
    data = _body(request)
    if data is None:
        return _erro('Informações inválidas.')
    enunciado = str(data.get('enunciado') or '').strip()
    materia_id = data.get('materia_id')
    alts = data.get('alts') or []
    if not materia_id or not Materia.objects.filter(pk=materia_id).exists():
        return _erro('Escolha uma matéria válida.', campo='materia_id')
    if not enunciado:
        return _erro('Escreva o enunciado.', campo='enunciado')
    erro_alts = _validar_alts(alts)
    if erro_alts:
        return _erro(erro_alts)
    q = Questao.objects.create(materia_id=materia_id, enunciado=enunciado, ativo=bool(data.get('ativo', True)))
    for i, a in enumerate(alts, start=1):
        Alternativa.objects.create(questao=q, texto=str(a['texto']).strip(), ordem_original=i,
                                    correta=bool(a.get('correta')))
    return JsonResponse(q.to_dict(), status=201)


@csrf_exempt
@require_http_methods(['PATCH', 'DELETE'])
def questao_detalhe(request, pk):
    q = get_object_or_404(Questao, pk=pk)
    em_uso = ProvaQuestao.objects.filter(questao_id=pk).exists()

    if request.method == 'DELETE':
        if em_uso:
            return _erro('Esta questão já foi usada em uma prova. Desative-a em vez de excluir.')
        q.delete()
        return JsonResponse({'ok': True})

    data = _body(request)
    if data is None:
        return _erro('Informações inválidas.')
    if 'alts' in data:
        erro_alts = _validar_alts(data['alts'])
        if erro_alts:
            return _erro(erro_alts)
        if em_uso and len(data['alts']) < q.alternativas.count():
            return _erro('Questão já usada em prova: não é possível remover alternativas.')
        q.alternativas.all().delete()
        for i, a in enumerate(data['alts'], start=1):
            Alternativa.objects.create(questao=q, texto=str(a['texto']).strip(), ordem_original=i,
                                        correta=bool(a.get('correta')))
    if 'materia_id' in data:
        q.materia_id = data['materia_id']
    if 'enunciado' in data:
        enunciado = str(data['enunciado']).strip()
        if not enunciado:
            return _erro('Escreva o enunciado.', campo='enunciado')
        q.enunciado = enunciado
    if 'ativo' in data:
        q.ativo = bool(data['ativo'])
    q.save()
    return JsonResponse(q.to_dict())



#PROVAS - GERAR VERSÃO
def _gerar_versao(prova, qids, embaralhar_questoes=True):
    ordem_q = list(qids)
    if embaralhar_questoes:
        random.shuffle(ordem_q)
    codigo = 'V-' + uuid_lib.uuid4().hex[:4].upper()
    versao = VersaoProva.objects.create(prova=prova, uuid=uuid_lib.uuid4(), codigo=codigo)
    for i, qid in enumerate(ordem_q, start=1):
        pq = ProvaQuestao.objects.create(versao_prova=versao, questao_id=qid, ordem=i)
        correta = Alternativa.objects.filter(questao_id=qid, correta=True).first()
        if correta:
            Gabarito.objects.create(versao_prova=versao, prova_questao=pq, alternativa=correta)
    return versao

#PROVAS
@csrf_exempt
@require_http_methods(['GET', 'POST'])
def provas(request):
    if request.method == 'GET':
        qs = Prova.objects.filter(professor_id=_professor_id(request)).order_by('-id')
        return JsonResponse([p.to_dict() for p in qs], safe=False)
    data = _body(request)
    if data is None:
        return _erro('Informações inválidas.')
    nome = str(data.get('nome') or '').strip()
    materia_id = data.get('materia_id')
    qids = data.get('qids') or []
    n_versoes = int(data.get('n_versoes') or 1)
    emb_q = bool(data.get('embaralhar_questoes', True))
    if not nome:
        return _erro('Dê um nome à prova.', campo='nome')
    if not materia_id or not Materia.objects.filter(pk=materia_id).exists():
        return _erro('Cadastre uma matéria antes.', campo='materia_id')
    if not qids:
        return _erro('Escolha pelo menos uma questão.')
    ativas = set(Questao.objects.filter(pk__in=qids, materia_id=materia_id, ativo=True).values_list('id', flat=True))
    if len(ativas) != len(set(qids)):
        return _erro('Uma ou mais questões escolhidas não existem ou não estão ativas nesta matéria.')
    if not (1 <= n_versoes <= 10):
        return _erro('Informe de 1 a 10 versões.')

    prova = Prova.objects.create(professor_id=_professor_id(request, data), materia_id=materia_id,
                                  nome=nome, descricao=str(data.get('descricao') or '').strip())
    versoes = [_gerar_versao(prova, qids, emb_q) for _ in range(n_versoes)]

    resposta = prova.to_dict()
    resposta['versoes'] = [v.to_dict() for v in versoes]
    return JsonResponse(resposta, status=201)


@csrf_exempt
@require_http_methods(['GET', 'DELETE'])
def prova_detalhe(request, pk):
    p = get_object_or_404(Prova, pk=pk)
    if request.method == 'GET':
        return JsonResponse(p.to_dict())
    if Avaliacao.objects.filter(versao_prova__prova_id=pk).exists():
        return _erro('Esta prova já foi aplicada a alunos e não pode ser excluída.')
    VersaoProva.objects.filter(prova_id=pk).delete()
    p.delete()
    return JsonResponse({'ok': True})

#GERAR VERSÕES
@csrf_exempt
@require_http_methods(['POST'])
def gerar_versoes(request, pk):
    """Nova(s) versão(ões) para uma prova já existente, com as mesmas questões da última versão."""
    prova = get_object_or_404(Prova, pk=pk)
    data = _body(request) or {}
    ultima = prova.versoes.order_by('-id').first()
    if not ultima:
        return _erro('Essa prova ainda não tem nenhuma versão com questões.')
    qids = list(ultima.itens.order_by('ordem').values_list('questao_id', flat=True))
    n_versoes = int(data.get('n_versoes') or 1)
    if not (1 <= n_versoes <= 10):
        return _erro('Informe de 1 a 10 versões.')
    versoes = [_gerar_versao(prova, qids, bool(data.get('embaralhar_questoes', True))) for _ in range(n_versoes)]
    return JsonResponse([v.to_dict() for v in versoes], safe=False, status=201)


@require_http_methods(['GET'])
def versao_detalhe(request, pk):
    v = get_object_or_404(VersaoProva, pk=pk)
    return JsonResponse(v.to_dict())


LETRAS = 'ABCDE'
#VERSÃO COMPLETA DA PROVA
def _versao_completa_json(v):
    prova = v.prova
    materia = prova.materia if prova else None
    gabarito_por_pq = {g.prova_questao_id: g.alternativa_id for g in Gabarito.objects.filter(versao_prova=v)}
    itens = []
    for it in v.itens.select_related('questao').order_by('ordem'):
        q = it.questao
        alts = list(q.alternativas.order_by('ordem_original')) if q else []
        alt_correta_id = gabarito_por_pq.get(it.id)
        correta_letra = None
        for i, a in enumerate(alts):
            if a.id == alt_correta_id:
                correta_letra = LETRAS[i] if i < len(LETRAS) else None
                break
        itens.append({
            'ordem': it.ordem,
            'enunciado': q.enunciado if q else '',
            'alternativas': [a.texto for a in alts],
            'correta_letra': correta_letra,
        })
    return {
        'id': v.id, 'codigo': v.codigo, 'uuid': str(v.uuid),
        'prova_nome': prova.nome if prova else '', 'prova_descricao': prova.descricao if prova else '',
        'materia_nome': materia.nome if materia else '',
        'itens': itens,
    }


@require_http_methods(['GET'])
def versao_completa(request, pk):
    """Versão pronta pra imprimir: texto da prova, das questões e das alternativas
    (não só os ids), mais a letra da alternativa correta de cada questão."""
    return JsonResponse(_versao_completa_json(get_object_or_404(VersaoProva, pk=pk)))


@require_http_methods(['GET'])
def versao_qr(request, pk):
    """PNG do QR code dessa versão (payload = FL1:<uuid em hex>). O frontend
    coloca essa imagem na folha da prova que ele mesmo imprime."""
    v = get_object_or_404(VersaoProva, pk=pk)
    payload = build_payload(v.uuid)
    png = qr_png_bytes(payload, box_size=6)
    return HttpResponse(png, content_type='image/png')


@require_http_methods(['GET'])
@_json_erros
def versao_por_uuid(request, uuid):
    """Mesma resposta de versao_completa, achada pelo UUID do QR da folha (com ou sem hífens).
    É daqui que o leitor tira a versão da prova e o gabarito."""
    try:
        uid = uuid_lib.UUID(uuid)
    except ValueError:
        return _erro('QR inválido.')
    v = VersaoProva.objects.filter(uuid=uid).first()
    if not v:
        return _erro('Essa versão de prova não existe neste sistema.', 404)
    return JsonResponse(_versao_completa_json(v))

#APLICAR PROVA
def _parse_data_aplicacao(valor):
    if not valor:
        return timezone.now()
    texto = str(valor).strip()
    d = parse_date(texto) if len(texto) <= 10 else None
    if d:
        return dt.datetime.combine(d, dt.time(12, 0), tzinfo=dt.timezone.utc)
    momento = parse_datetime(texto)
    if momento is None:
        raise ValueError('Data de aplicação inválida.')
    return momento if timezone.is_aware(momento) else timezone.make_aware(momento)


@csrf_exempt
@require_http_methods(['POST'])
@_json_erros
def aplicar_prova(request, pk):
    prova = get_object_or_404(Prova, pk=pk)
    data = _body(request)
    if data is None:
        return _erro('Informações inválidas.')
    turma = Turma.objects.filter(pk=data.get('turma_id') or 0).first()
    if not turma:
        return _erro('Escolha uma turma válida.', campo='turma_id')
    versoes = list(prova.versoes.order_by('id'))
    if not versoes:
        return _erro('Gere ao menos uma versão desta prova antes de aplicar.')

    alunos_qs = Aluno.objects.filter(turma_id=turma.id)
    if data.get('aluno_id'):
        alunos_qs = alunos_qs.filter(pk=data['aluno_id'])
        if not alunos_qs.exists():
            return _erro('Esse aluno não pertence à turma escolhida.', campo='aluno_id')
    alunos_turma = list(alunos_qs.order_by('id'))
    if not alunos_turma:
        return _erro('Essa turma ainda não tem alunos. Cadastre em Turmas e alunos.')

    try:
        data_aplicacao = _parse_data_aplicacao(data.get('data_aplicacao'))
    except ValueError as exc:
        return _erro(str(exc), campo='data_aplicacao')

    pendentes = set(Avaliacao.objects.filter(versao_prova__prova=prova, status='aplicada',
                                             aluno_id__in=[a.id for a in alunos_turma])
                    .values_list('aluno_id', flat=True))
    # o rodízio continua de onde parou: aplicar de novo não manda sempre a versão 1
    deslocamento = Avaliacao.objects.filter(versao_prova__prova=prova).count()
    criadas, ignoradas = [], 0
    with transaction.atomic():
        for aluno in alunos_turma:
            if aluno.id in pendentes:
                ignoradas += 1
                continue
            versao = versoes[(deslocamento + len(criadas)) % len(versoes)]
            criadas.append(Avaliacao.objects.create(versao_prova=versao, aluno=aluno,
                                                    data_aplicacao=data_aplicacao, status='aplicada'))
    return JsonResponse({'criadas': [a.to_dict(com_respostas=False) for a in criadas],
                         'ignoradas': ignoradas}, status=201)

#AVALIAÇÕES APLICADAS
@require_http_methods(['GET'])
@_json_erros
def avaliacoes(request):
    qs = Avaliacao.objects.select_related('aluno__turma', 'versao_prova__prova')
    for param, campo in (('versao_prova_id', 'versao_prova_id'), ('aluno_id', 'aluno_id'),
                         ('turma_id', 'aluno__turma_id'), ('prova_id', 'versao_prova__prova_id'),
                         ('professor_id', 'versao_prova__prova__professor_id'), ('status', 'status')):
        valor = request.GET.get(param)
        if valor:
            qs = qs.filter(**{campo: valor})
    return JsonResponse([a.to_dict(com_respostas=False) for a in qs.order_by('-id')], safe=False)


@csrf_exempt
@require_http_methods(['GET', 'DELETE'])
@_json_erros
def avaliacao_detalhe(request, pk):
    av = get_object_or_404(Avaliacao.objects.select_related('aluno__turma', 'versao_prova__prova'), pk=pk)
    if request.method == 'DELETE':
        av.delete()
        return JsonResponse({'ok': True})
    return JsonResponse(av.to_dict())

#SALVAR RESULTADO DA LEITURA (folha lida pelo celular)
@csrf_exempt
@require_http_methods(['POST'])
@_json_erros
def salvar_resultado(request, pk):
    av = get_object_or_404(Avaliacao.objects.select_related('aluno__turma', 'versao_prova__prova'), pk=pk)
    data = _body(request)
    if data is None:
        return _erro('Informações inválidas.')
    letras = data.get('respostas')
    if not isinstance(letras, list):
        return _erro('Envie a lista de respostas lidas.', campo='respostas')

    versao = av.versao_prova
    uuid_folha = str(data.get('uuid') or '').replace('-', '').lower()
    if uuid_folha and uuid_folha != versao.uuid.hex:
        return _erro(f'Esta folha é de outra versão da prova. A avaliação de {av.aluno.nome} é da '
                     f'versão {versao.codigo}. Confira se escolheu o aluno certo.', 409, 'uuid')

    itens = list(versao.itens.select_related('questao').order_by('ordem'))
    if not itens:
        return _erro('Esta versão não tem questões.')
    if len(letras) != len(itens):
        return _erro(f'A leitura trouxe {len(letras)} respostas, mas a prova tem {len(itens)} questões.',
                     campo='respostas')
    gabarito = {g.prova_questao_id: g.alternativa_id for g in Gabarito.objects.filter(versao_prova=versao)}

    with transaction.atomic():
        av.respostas.all().delete()
        acertos = 0
        for item, letra in zip(itens, letras):
            letra = str(letra or '').strip().upper()
            alts = list(item.questao.alternativas.order_by('ordem_original'))   # mesma ordem de versao_completa
            # len(letra) == 1: sem isso '' e 'BC' passariam em `in 'ABCDE'` (substring) e virariam A/B
            idx = LETRAS.index(letra) if len(letra) == 1 and letra in LETRAS else None
            marcada = alts[idx] if idx is not None and idx < len(alts) else None
            correta = bool(marcada and gabarito.get(item.id) == marcada.id)
            acertos += correta
            Resposta.objects.create(avaliacao=av, prova_questao=item, alternativa=marcada, correta=correta)
        av.nota = round(acertos * 10.0 / len(itens), 2)
        av.status = 'corrigida'
        av.data_correcao = timezone.now()
        av.save()

    corpo = av.to_dict(com_respostas=False)
    corpo.update({'acertos': acertos, 'total': len(itens)})
    return JsonResponse(corpo)