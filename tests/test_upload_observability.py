import asyncio

from backend.app.core.upload_observability import UploadObservability


def test_logs_entry_before_body_and_preserves_stream(monkeypatch):
    events = []
    monkeypatch.setattr('backend.app.core.upload_observability.emit', lambda event, **fields: events.append(event))
    messages = iter([
        {'type': 'http.request', 'body': b'abc', 'more_body': True},
        {'type': 'http.request', 'body': b'def', 'more_body': False},
    ])
    async def receive():
        assert events[0] == '[UPLOAD] Request entered'
        return next(messages)
    sent = []
    async def send(message):
        sent.append(message)
    async def app(scope, receive, send):
        assert (await receive())['body'] == b'abc'
        assert (await receive())['body'] == b'def'
        assert '[UPLOAD] Body completed' in events
        await send({'type': 'http.response.start', 'status': 201, 'headers': []})
        await send({'type': 'http.response.body', 'body': b'ok'})
    asyncio.run(UploadObservability(app)(
        {'type': 'http', 'method': 'POST', 'path': '/api/v1/documents', 'headers': []}, receive, send))
    assert sent[0]['status'] == 201
    assert sent[1]['body'] == b'ok'
