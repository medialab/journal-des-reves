import logging
import time


access_logger = logging.getLogger('django.access')


class RequestAuditLogMiddleware:
    """Log each HTTP request/response pair for security audits."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started_at = time.perf_counter()
        response = self.get_response(request)
        duration_ms = int((time.perf_counter() - started_at) * 1000)

        user_id = 'anonymous'
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            user_id = str(user.pk)

        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        client_ip = forwarded_for.split(',')[0].strip() if forwarded_for else request.META.get('REMOTE_ADDR', '-')

        access_logger.info(
            'method=%s path=%s status=%s duration_ms=%s ip=%s user_id=%s',
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            client_ip,
            user_id,
        )

        return response
