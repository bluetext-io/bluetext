import httpx
from datetime import datetime
import json

from ..utils import log

logger = log.get_logger(__name__)

def ppr_header_key(k):
    return '-'.join(word.capitalize() for word in k.split('-'))

def ppr_headers(headers):
    if headers:
        return '\n'.join(f'{log.cyan(ppr_header_key(k))}: {v}'
                         for (k, v) in headers.items())

class AsyncClient(httpx.AsyncClient):
    async def request(self, *args, **kwargs):
        method = kwargs.get("method", args[0] if args else "GET")
        url = kwargs.get("url", args[1] if len(args) > 1 else "")
        req_str = log.magenta(f'HTTP {method} {url}')
        is_debug = logger.isEnabledFor(log.DEBUG)
        is_trace = is_debug and logger.isEnabledFor(log.TRACE)
        if j := kwargs.get('json'):
            if not isinstance(kwargs.get('headers'), dict):
                kwargs['headers'] = {}
            kwargs['headers']['Content-Type'] = 'application/json'
            del kwargs['json']
            kwargs['data'] = json.dumps(j)
        if is_trace:
            headers = ppr_headers(kwargs.get('headers', {}))
            body = kwargs.get('data')
            logger.trace('Sent %s:%s%s%s%s',
                         req_str,
                         "\n" if headers else "",
                         headers or '',
                         "\n" if body else "",
                         body or '')
        elif is_debug:
            logger.debug(f"Sent {req_str}")
        now = datetime.now()
        try:
            response = await super().request(*args, **kwargs)
            code = response.status_code
            code_str = f"HTTP {code}"
            if 400 <= code <= 599:
                code_str = log.yellow(code_str)
            elif 100 <= code <= 399:
                code_str = log.green(code_str)
            else:
                code_str = log.red(code_str)
            time_ms = int((datetime.now() - now).total_seconds() * 1000)
            msg = f'Got {code_str} for {req_str} in {log.cyan(time_ms)} ms'
            if is_trace:
                headers = ppr_headers(response.headers)
                body = response.text
                logger.trace('%s:%s%s%s%s',
                             msg,
                             "\n" if headers else "",
                             headers or '',
                             "\n" if body else "",
                             body or '')
            elif is_debug:
                logger.debug(msg)
            return response
        except Exception as e:
            time_ms = int((datetime.now() - now).total_seconds() * 1000)
            msg = f'Got {log.red("HTTP ERROR")} for {req_str} in {log.cyan(time_ms)} ms'
            if is_trace:
                logger.trace(f'{msg}: {log.red(str(e))}')
            elif is_debug:
                logger.debug(msg)
            raise
