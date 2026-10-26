"""Backend de e-mail via API HTTP do Brevo (https://www.brevo.com).

Por que existe: o plano gratuito do Render BLOQUEIA as portas SMTP (25/465/587),
então o `send_mail` com Gmail/SMTP dá timeout em produção. Esta classe envia pela
API HTTPS (porta 443), que não é bloqueada. Não precisa instalar nada novo —
usa só a biblioteca padrão.

Ativação: defina BREVO_API_KEY (e DEFAULT_FROM_EMAIL com um remetente verificado
no Brevo) nas variáveis de ambiente. Veja settings.py.
"""
import json
import logging
import urllib.error
import urllib.request
from email.utils import parseaddr

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

BREVO_URL = 'https://api.brevo.com/v3/smtp/email'


class BrevoAPIBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        enviados = 0
        for msg in email_messages:
            try:
                self._enviar(msg)
                enviados += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return enviados

    def _enviar(self, msg):
        nome, email = parseaddr(msg.from_email or settings.DEFAULT_FROM_EMAIL)
        remetente = {'email': email}
        if nome:
            remetente['name'] = nome

        payload = {
            'sender': remetente,
            'to': [{'email': dest} for dest in msg.to],
            'subject': msg.subject,
            'textContent': msg.body,
        }
        req = urllib.request.Request(
            BREVO_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'api-key': settings.BREVO_API_KEY,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=settings.EMAIL_TIMEOUT) as resp:
                resp.read()
        except urllib.error.HTTPError as exc:
            # inclui o motivo devolvido pelo Brevo (ex.: remetente não verificado)
            detalhe = exc.read().decode('utf-8', 'replace')[:500]
            raise RuntimeError(f'Brevo recusou o envio (HTTP {exc.code}): {detalhe}') from exc
