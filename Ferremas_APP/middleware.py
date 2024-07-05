from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin

class CustomCSRFMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if hasattr(exception, 'csrf_token'):
            return render(request, 'pages/errors/csrf_error.html', status=403)
        return None
