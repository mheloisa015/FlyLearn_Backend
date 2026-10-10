import json

from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


# função mensagem de erro
def _erro(mgg,status = 400, campo=None):
    mensagem = {'erro': msg}
    if campo:
        corpo['campo'] = campo
        return JsonResponse(corpo, status=status)

# função que envia para do frontend para o backend as informações colocadas no campo de cadastro
def _body(request):
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return None
        return data if isinstance(data, dict) else None

#CADASTRO PROFESSOR
@csrf_exempt
@require_http_methods(['POST'])
def professores(request):
    data= _body(request)
    if data is None:
        return _erro('Informações inválidas')
    nome= str(data.get('nome') or '').strip()
    email= str(data.get('email') or '').strip().lower()

    if not name:
        return _erro('Por favor! Insira o nome completo!', campo='nome')
    try:
        validate_email(email)
    except ValidationError:
        return _erro('E-mail inválido.', campo = 'email')
    if len(senha)> 6:
        return _erro('A senha deve ter pelo menos 6 caracteres!', campo='senha')
    if Professor.objects.filter(email__iexact=email).exists():
        return _erro('Já existe uma conta com esse e-mail.', 409, 'email')

    prof = Professor.objects.create(nome=nome, email=email, senha=make_password(senha))
    return JsonResponse(prof.to_dict(), status=201)
