"""Recuperação de senha do professor.

Usa um token ASSINADO e sem estado (django.core.signing), então não precisa de
tabela nova nem de migration — importante porque os models deste projeto são
`managed = False` (o banco é criado fora do Django).

Propriedades de segurança:
  * expira em settings.RESET_SENHA_MAX_AGE segundos;
  * carrega uma "impressão digital" do hash da senha atual: assim que a senha é
    trocada, o token (e qualquer outro emitido antes) deixa de valer — uso único;
  * o link usa settings.FRONTEND_URL fixo, nunca o header Origin/Host da requisição
    (evita que um atacante faça o e-mail apontar para um site dele).
"""
import hashlib
import hmac
import logging
import threading
from urllib.parse import urlencode

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils.crypto import salted_hmac

from core.models import Professor

logger = logging.getLogger(__name__)

_SALT = 'flylearn.recuperacao-senha.v1'


def _impressao_digital(professor):
    """Muda sempre que a senha muda; não revela o hash (HMAC truncado)."""
    return salted_hmac(_SALT, professor.senha or '').hexdigest()[:24]


def gerar_token(professor):
    return signing.dumps({'id': professor.id, 'f': _impressao_digital(professor)}, salt=_SALT)


def professor_do_token(token):
    """Devolve o Professor se o token for válido, não expirado e ainda não usado; senão None."""
    if not token or not isinstance(token, str):
        return None
    try:
        dados = signing.loads(token, salt=_SALT, max_age=settings.RESET_SENHA_MAX_AGE)
        professor = Professor.objects.filter(pk=dados['id']).first()
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        return None
    if not professor or not professor.ativo:
        return None
    if not hmac.compare_digest(dados.get('f', ''), _impressao_digital(professor)):
        return None  # senha já foi alterada depois que o token foi emitido
    return professor


def montar_link(professor):
    return f"{settings.FRONTEND_URL}/recup_senha.html?{urlencode({'token': gerar_token(professor)})}"


def limite_excedido(email):
    """Limita pedidos por e-mail (evita usar o sistema para spammar alguém).
    Usa o cache do Django; com vários workers o LocMemCache é por processo, então é
    uma proteção aproximada — configure CACHES com Redis/DB se precisar de rigor."""
    chave = 'recup-senha:' + hashlib.sha256(email.encode()).hexdigest()
    janela = settings.RESET_SENHA_JANELA
    cache.add(chave, 0, janela)
    try:
        total = cache.incr(chave)
    except ValueError:  # expirou entre o add e o incr
        cache.set(chave, 1, janela)
        total = 1
    return total > settings.RESET_SENHA_MAX_PEDIDOS


def _enviar(professor, link):
    minutos = settings.RESET_SENHA_MAX_AGE // 60
    nome = (professor.nome or '').split(' ')[0] or 'professor(a)'
    corpo = (
        f'Olá, {nome}!\n\n'
        'Recebemos um pedido para redefinir a senha da sua conta no FlyLearn.\n'
        f'Use o link abaixo (válido por {minutos} minutos e de uso único):\n\n'
        f'{link}\n\n'
        'Se você não fez esse pedido, pode ignorar este e-mail — sua senha continua a mesma.\n\n'
        '— Equipe FlyLearn'
    )
    try:
        send_mail('Redefinição de senha — FlyLearn', corpo, settings.DEFAULT_FROM_EMAIL,
                  [professor.email], fail_silently=False)
    except Exception:  # noqa: BLE001 — nunca propagar: a resposta da API não pode variar
        logger.exception('Falha ao enviar e-mail de recuperação (professor id=%s)', professor.id)


def enviar_email_em_segundo_plano(professor):
    """Envia em thread para a resposta da API demorar igual exista a conta ou não
    (senão o tempo de resposta revelaria quais e-mails estão cadastrados)."""
    link = montar_link(professor)
    threading.Thread(target=_enviar, args=(professor, link), daemon=True).start()
