import json

from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Professor


# monta a resposta de erro que o frontend recebe
def _erro(msg, status=400, campo=None):
    corpo = {'erro': msg}
    if campo:
        corpo['campo'] = campo
    return JsonResponse(corpo, status=status)


# lê o JSON que o frontend enviou (nome, email, senha)
def _body(request):
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


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

#LOGIN
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
    return JsonResponse (prof.to_dict())