"""Bounded HTTP metrics and content-free logs. No request-supplied correlation IDs."""
import json
import logging
import time
import uuid
from datetime import datetime, timezone

from jobfit.observability.metrics import safely, bounded


class SafeJSONFormatter(logging.Formatter):
    def format(self, record):
        # Never format message, arguments, stack/exception or arbitrary extras.
        row = {'timestamp': datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
               'level': record.levelname,
               'event': 'application_event'}
        if getattr(record, '_jobfit_http', False):
            row.update(event='http_completed', request_id=record.safe_request_id,
                       route=record.safe_route, status=record.safe_status,
                       duration_ms=record.safe_duration_ms)
        elif getattr(record, '_jobfit_analysis', False):
            row.update(event='analysis_finished', outcome=record.safe_outcome)
            if hasattr(record, 'safe_request_id'):
                row['request_id'] = record.safe_request_id
        elif getattr(record, '_jobfit_stage', False):
            row.update(event='stage_completed', stage=record.safe_stage, outcome=record.safe_outcome,
                       duration_ms=record.safe_duration_ms)
            if hasattr(record, 'safe_error_code'):
                row['error_code'] = record.safe_error_code
        return json.dumps(row, separators=(',', ':'))


def configure_logging():
    """App factory only. Scope to jobfit; disable unsafe server access/exception rendering."""
    for name in ('jobfit', 'uvicorn.error', 'uvicorn.access'):
        logger = logging.getLogger(name)
        if not any(getattr(h, '_jobfit_safe', False) for h in logger.handlers):
            handler = logging.StreamHandler()
            handler._jobfit_safe = True
            handler.setFormatter(SafeJSONFormatter())
            logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(logging.INFO)


class HTTPMetrics:
    def __init__(self, app, telemetry, routes):
        self.app, self.telemetry, self.routes = app, telemetry, routes

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        start, status = time.monotonic(), 500
        scope['jobfit_request_id'] = uuid.uuid4().hex

        async def response(message):
            nonlocal status
            if message['type'] == 'http.response.start':
                status = message['status']
            await send(message)
        try:
            await self.app(scope, receive, response)
        finally:
            route = getattr(scope.get('route'), 'path', None)
            allowed = {r.path for r in self.routes if hasattr(r, 'path')}
            route = route if route in allowed else 'unmatched'
            method = bounded(scope.get('method'), {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'})
            duration = time.monotonic() - start
            safely(self.telemetry.request, method, route, status, duration,
                   bool(scope.get('jobfit_analysis_duplicate')))
            # Skip successful polling and scraping in logs; metrics still record them.
            if method != 'GET' or status >= 400:
                safely(logging.getLogger('jobfit.http').info, 'http_completed', extra={
                    '_jobfit_http': True, 'safe_request_id': scope['jobfit_request_id'], 'safe_route': route,
                    'safe_status': status, 'safe_duration_ms': round(duration * 1000, 3)})
