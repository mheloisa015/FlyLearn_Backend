"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

#Esse arquivo eh responsavel por ser o ponto de entrada da especificacao WSGI(Web Server Gateway Interface) de projeto Django
#Utilizado por servidores web para se comunicar com Python

import os
#inicializa a aplicação e retornando callble
from django.core.wsgi import get_wsgi_application

#Define a variável de ambiente que indica ao Django onde encontrar o arquivo de config do projeto config/settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
