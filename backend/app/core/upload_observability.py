"""Upload diagnostics emitted directly to the configured Uvicorn error logger."""
import json
import logging
import os
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

request_id = ContextVar('upload_request_id', default=None)
logger = logging.getLogger('uvicorn.error')


def resources():
    result = {}
    try:
        for line in Path('/proc/self/status').read_text().splitlines():
            if line.startswith(('VmRSS:', 'VmHWM:')):
                key, value = line.split(':', 1)
                result[key + '_kb'] = int(value.split()[0])
    except (OSError, ValueError):
        pass
    for name in ('memory.current', 'memory.peak', 'memory.max', 'memory.events', 'cpu.stat'):
        try:
            result[name] = (Path('/sys/fs/cgroup') / name).read_text().strip()
        except OSError:
            pass
    return result


def emit(event, **fields):
    logger.info('%s %s', event, json.dumps({
        'request_id': request_id.get(), 'pid': os.getpid(),
        'commit': os.environ.get('RENDER_GIT_COMMIT'),
        'unix_time': time.time(), **resources(), **fields,
    }))


@contextmanager
def phase(name):
    started = time.monotonic()
    emit('[PIPELINE] ' + name + ' started')
    try:
        yield
    except BaseException:
        emit('[PIPELINE] ' + name + ' failed', elapsed_s=time.monotonic() - started)
        raise
    else:
        emit('[PIPELINE] ' + name + ' completed', elapsed_s=time.monotonic() - started)


class UploadObservability:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if not (scope['type'] == 'http' and scope['method'] == 'POST'
                and scope['path'].rstrip('/').endswith('/documents')):
            return await self.app(scope, receive, send)
        headers = dict(scope.get('headers', []))
        rid = headers.get(b'x-request-id') or headers.get(b'rndr-id')
        token = request_id.set(rid.decode('latin1')[:200] if rid else str(uuid.uuid4()))
        total = 0
        started = time.monotonic()
        try:
            emit('[UPLOAD] Request entered', content_length=headers.get(b'content-length', b'').decode('latin1'),
                 cf_ray=headers.get(b'cf-ray', b'').decode('latin1'))
            async def observed_receive():
                nonlocal total
                message = await receive()
                if message['type'] == 'http.request':
                    total += len(message.get('body', b''))
                    if not message.get('more_body', False):
                        emit('[UPLOAD] Body completed', bytes_received=total)
                elif message['type'] == 'http.disconnect':
                    emit('[UPLOAD] Client disconnected', bytes_received=total)
                return message
            async def observed_send(message):
                if message['type'] == 'http.response.start':
                    emit('[UPLOAD] Response started', status=message['status'], elapsed_s=time.monotonic() - started)
                await send(message)
            await self.app(scope, observed_receive, observed_send)
        except BaseException:
            emit('[UPLOAD] Request failed', elapsed_s=time.monotonic() - started)
            raise
        finally:
            request_id.reset(token)
