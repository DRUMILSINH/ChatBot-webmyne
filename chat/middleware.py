import uuid


class TraceIdMiddleware:
    """
    Adds a per-request trace ID for audit logging and debugging.
    """

    header_name = "HTTP_X_TRACE_ID"
    response_header = "X-Trace-Id"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        trace_id = request.META.get(self.header_name) or uuid.uuid4().hex
        request.trace_id = trace_id
        response = self.get_response(request)
        response[self.response_header] = trace_id
        return response
