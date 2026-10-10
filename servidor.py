import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / 'omr'))   # o app_web.py importa corretor, qr_util etc. como módulos soltos

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application  # noqa: E402
from app_web import app as flask_app               # noqa: E402

django_app = get_wsgi_application()
ROTAS_DJANGO = ('/professores', '/admin', '/static')


def application(environ, start_response):
    caminho = environ.get('PATH_INFO', '')
    if caminho.startswith(ROTAS_DJANGO):
        return django_app(environ, start_response)
    return flask_app(environ, start_response)
