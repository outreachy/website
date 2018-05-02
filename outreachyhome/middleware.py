from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

class XForwardedForMiddleware(object):
    def __init__(self, get_response):
        self.trusted_proxies = getattr(settings, 'TRUSTED_PROXIES', None)
        if not self.trusted_proxies:
            raise MiddlewareNotUsed
        self.get_response = get_response

    def __call__(self, request):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded and request.META.get('REMOTE_ADDR') in self.trusted_proxies:
            request.META['REMOTE_ADDR'] = forwarded.split(',')[-1].strip()
        return self.get_response(request)
