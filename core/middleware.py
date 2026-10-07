from django.conf import settings
from django.http import HttpResponse


class SimpleCorsMiddleware:
    """CORS mínimo (sem dependência extra). Origens em settings.CORS_ALLOWED_ORIGINS.
    Em produção o Netlify já faz proxy de /api/*, então normalmente nem é necessário."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get('Origin')
        permitido = origin and origin in getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        if request.method == 'OPTIONS' and permitido:
            resp = HttpResponse(status=204)
        else:
            resp = self.get_response(request)
        if permitido:
            resp['Access-Control-Allow-Origin'] = origin
            resp['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            resp['Access-Control-Allow-Headers'] = 'Content-Type'
            resp['Vary'] = 'Origin'
        return resp
