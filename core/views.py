import json
import random
import uuid as uuid_lib

from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import (
    Aluno, Alternativa, Avaliacao, Gabarito, Materia, Prova, ProvaQuestao,
    Professor, Questao, Resposta, Turma, VersaoProva,
)


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


# Enquanto não há login por token/sessão, o professor_id vem do próprio front
# (query string em GET, corpo em POST) e cai no professor de teste (id 1) se
# não for informado.
def _professor_id(request, data=None):
    bruto = (data or {}).get('professor_id') or request.GET.get('professor_id')
    try:
        return int(bruto)
    except (TypeError, ValueError):
        return 1


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


# ---------------------------------------------------------------------------
# MATÉRIAS
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(['GET', 'POST'])
def materias(request):
    if request.method == 'GET':
        qs = Materia.objects.filter(professor_id=_professor_id(request)).order_by('nome')
        return JsonResponse([m.to_dict() for m in qs], safe=False)

    data = _body(request)
    if data is None:
        return _erro('Informações inválidas.')
    nome = str(data.get('nome') or '').strip()
    if not nome:
        return _erro('Informe o nome da matéria.', campo='nome')
    pid = _professor_id(request, data)
    if Materia.objects.filter(professor_id=pid, nome__iexact=nome).exists():
        return _erro('Você já tem uma matéria com esse nome.', 409, 'nome')
    m = Materia.objects.create(professor_id=pid, nome=nome, descricao=str(data.get('descricao') or '').strip())
    return JsonResponse(m.to_dict(), status=201)


@csrf_exempt
@require_http_methods(['PATCH', 'DELETE'])
def materia_detalhe(request, pk):
    m = get_object_or_404(Materia, pk=pk)
    if request.method == 'DELETE':
        if Questao.objects.filter(materia_id=pk).exists() or Prova.objects.filter(materia_id=pk).exists():
            return _erro('Não é possível excluir: há questões ou provas vinculadas a esta matéria.')
        m.delete()
        return JsonResponse({'ok': True})

    data = _body(request)
    if data is None:
        return _erro('Informações inválidas.')
    if 'nome' in data:
        nome = str(data['nome']).strip()
        if not nome:
            return _erro('Informe o nome da matéria.', campo='nome')
        m.nome = nome
    if 'descricao' in data:
        m.descricao = str(data['descricao']).strip()
    m.save()
    return JsonResponse(m.to_dict())


# ---------------------------------------------------------------------------
# TURMAS E ALUNOS
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(['GET', 'POST'])
def turmas(request):
    if request.method == 'GET':
        qs = Turma.objects.filter(professor_id=_professor_id(request)).order_by('ano', 'disciplina')
        return JsonResponse([t.to_dict() for t in qs], safe=False)

    data = _body(request)
    if data is None:
        return _erro('Informações inválidas.')
    disciplina = str(data.get('disciplina') or '').strip()
    if not disciplina:
        return _erro('Informe a disciplina da turma.', campo='disciplina')
    try:
        ano = int(data.get('ano'))
    except (TypeError, ValueError):
        return _erro('Informe o ano/série da turma.', campo='ano')
    t = Turma.objects.create(professor_id=_professor_id(request, data), ano=ano, disciplina=disciplina)
    return JsonResponse(t.to_dict(), status=201)


@csrf_exempt
@require_http_methods(['PATCH', 'DELETE'])
def turma_detalhe(request, pk):
    t = get_object_or_404(Turma, pk=pk)
    if request.method == 'DELETE':
        if Aluno.objects.filter(turma_id=pk).exists():
            return _erro('Não é possível excluir: há alunos nesta turma.')
        t.delete()
        return JsonResponse({'ok': True})

    data = _body(request)
    if data is None:
        return _erro('Informações inválidas.')
    if 'ano' in data:
        try:
            t.ano = int(data['ano'])
        except (TypeError, ValueError):
            return _erro('Ano inválido.', campo='ano')
    if 'disciplina' in data:
        t.disciplina = str(data['disciplina']).strip()
    t.save()
    return JsonResponse(t.to_dict())


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def alunos(request):
    if request.method == 'GET':
        qs = Aluno.objects.all()
        turma_id = request.GET.get('turma_id')
        if turma_id:
            qs = qs.filter(turma_id=turma_id)
        return JsonResponse([a.to_dict() for a in qs.order_by('nome')], safe=False)

    data = _body(request)
    if data is None:
        return _erro('Informações inválidas.')
    nome = str(data.get('nome') or '').strip()
    turma_id = data.get('turma_id')
    if not nome:
        return _erro('Informe o nome do aluno.', campo='nome')
    if not turma_id or not Turma.objects.filter(pk=turma_id).exists():
        return _erro('Escolha uma turma válida.', campo='turma_id')
    try:
        ra = int(data.get('ra'))
    except (TypeError, ValueError):
        return _erro('Informe o RA do aluno.', campo='ra')
    a = Aluno.objects.create(turma_id=turma_id, nome=nome, ra=ra, email=str(data.get('email') or '').strip())
    return JsonResponse(a.to_dict(), status=201)


@csrf_exempt
@require_http_methods(['PATCH', 'DELETE'])
def aluno_detalhe(request, pk):
    a = get_object_or_404(Aluno, pk=pk)
    if request.method == 'DELETE':
        if Avaliacao.objects.filter(aluno_id=pk).exists():
            return _erro('Este aluno já tem avaliações aplicadas e não pode ser excluído.')
        a.delete()
        return JsonResponse({'ok': True})

    data = _body(request)
    if data is None:
        return _erro('Informações inválidas.')
    if 'nome' in data:
        a.nome = str(data['nome']).strip()
    if 'ra' in data:
        try:
            a.ra = int(data['ra'])
        except (TypeError, ValueError):
            return _erro('RA inválido.', campo='ra')
    if 'email' in data:
        a.email = str(data['email']).strip()
    if 'turma_id' in data:
        a.turma_id = data['turma_id']
    a.save()
    return JsonResponse(a.to_dict())


# ---------------------------------------------------------------------------
# BANCO DE QUESTÕES (questão + alternativas)
# ---------------------------------------------------------------------------

def _validar_alts(alts):
    if not isinstance(alts, list) or len(alts) < 2 or len(alts) > 5:
        return 'Informe de 2 a 5 alternativas.'
    if any(not str(a.get('texto') or '').strip() for a in alts):
        return 'Preencha o texto de todas as alternativas.'
    if not any(a.get('correta') for a in alts):
        return 'Marque a alternativa correta.'
    return None


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


# ---------------------------------------------------------------------------
# PROVAS, VERSÕES E GABARITO
#
# Cada versão (versao_prova) tem seu próprio conjunto de prova_questao
# (questão + ordem NESSA versão) e seu próprio gabarito (prova_questao ->
# alternativa correta, fixado no momento da geração). A ordem das ALTERNATIVAS
# não é embaralhada por versão nesse banco — a letra de cada alternativa é
# sempre a posição ordem_original dela.
# ---------------------------------------------------------------------------

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


@require_http_methods(['GET'])
def versao_completa(request, pk):
    """Versão pronta pra imprimir: texto da prova, das questões e das alternativas
    (não só os ids), mais a letra da alternativa correta de cada questão."""
    v = get_object_or_404(VersaoProva, pk=pk)
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

    return JsonResponse({
        'id': v.id, 'codigo': v.codigo, 'uuid': str(v.uuid),
        'prova_nome': prova.nome if prova else '', 'prova_descricao': prova.descricao if prova else '',
        'materia_nome': materia.nome if materia else '',
        'itens': itens,
    })


@csrf_exempt
@require_http_methods(['POST'])
def aplicar_prova(request, pk):
    """Cria uma avaliação por aluno da turma, distribuindo as versões existentes da prova."""
    prova = get_object_or_404(Prova, pk=pk)
    data = _body(request)
    if data is None:
        return _erro('Informações inválidas.')
    turma_id = data.get('turma_id')
    turma = Turma.objects.filter(pk=turma_id).first()
    if not turma:
        return _erro('Escolha uma turma válida.', campo='turma_id')
    versoes = list(prova.versoes.all())
    if not versoes:
        return _erro('Gere ao menos uma versão desta prova antes de aplicar.')
    alunos_turma = list(Aluno.objects.filter(turma_id=turma_id).order_by('id'))
    if not alunos_turma:
        return _erro('Essa turma ainda não tem alunos. Cadastre em Turmas e alunos.')

    data_aplicacao = data.get('data_aplicacao') or None
    criadas = []
    for i, aluno in enumerate(alunos_turma):
        av = Avaliacao.objects.create(versao_prova=versoes[i % len(versoes)], aluno=aluno,
                                       data_aplicacao=data_aplicacao, status='aplicada')
        criadas.append(av)
    return JsonResponse([a.to_dict() for a in criadas], safe=False, status=201)


@require_http_methods(['GET'])
def avaliacoes(request):
    qs = Avaliacao.objects.all()
    versao_id = request.GET.get('versao_prova_id')
    aluno_id = request.GET.get('aluno_id')
    if versao_id:
        qs = qs.filter(versao_prova_id=versao_id)
    if aluno_id:
        qs = qs.filter(aluno_id=aluno_id)
    return JsonResponse([a.to_dict() for a in qs.order_by('-id')], safe=False)