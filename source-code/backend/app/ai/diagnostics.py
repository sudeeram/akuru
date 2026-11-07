"""Opt-in, bounded local model diagnostics. Never log SDK clients or credentials."""
import contextvars
import hashlib
import json
import logging
import os
import re
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings

_context = contextvars.ContextVar('akuru_ai_diagnostics', default=None)
logger = logging.getLogger(__name__)
_SECRET = re.compile(r'(?:password|api[_-]?key|authorization|cookie|csrf|access[_-]?token|refresh[_-]?token|client[_-]?secret|private[_-]?key|image_data_url)', re.I)


def _clean(value, settings):
    if isinstance(value, dict):
        return {str(k): '[REDACTED]' if _SECRET.search(str(k)) else _clean(v, settings) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v, settings) for v in value]
    if not isinstance(value, str):
        return value if value is None or isinstance(value, (bool, int, float)) else type(value).__name__
    if value.lstrip().startswith(('{','[')):
        try:
            decoded = json.loads(value)
            if isinstance(decoded,(dict,list)): return json.dumps(_clean(decoded,settings),ensure_ascii=False)
        except (ValueError,TypeError): pass
    secrets = [settings.openai_api_key, settings.operations_token, *settings.openai_account_keys.values()]
    known = [s.get_secret_value() for s in secrets if s]
    known.append(settings.database_password)
    for secret in known:
        if secret: value = value.replace(secret, '[REDACTED]')
    value = re.sub(r'\bsk-[A-Za-z0-9_-]{6,}', '[REDACTED]', value)
    value = re.sub(r'(?i)\bBearer\s+[^\s"<>]+', 'Bearer [REDACTED]', value)
    return re.sub(r'data:image/[^\s"<>]+', '[IMAGE OMITTED]', value)


def _write(settings, event):
    """Lock rotation across API/worker processes; every file is private."""
    import fcntl
    directory = Path(settings.ai_diagnostics_directory)
    if not directory.is_absolute() or directory.is_symlink():
        raise OSError('Unsafe diagnostics directory')
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(directory, 0o700)
    lock = os.open(directory / '.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = directory / 'model-calls.jsonl'
        files = [path, *(directory / f'model-calls.jsonl.{i}' for i in range(1, 6))]
        for candidate in files:
            if candidate.is_symlink(): raise OSError('Unsafe diagnostics file')
            if candidate.exists() and candidate.stat().st_mtime < time.time() - settings.ai_diagnostics_retention_days * 86400:
                candidate.unlink()
        encoded = (json.dumps(event, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
        if path.exists() and path.stat().st_size + len(encoded) > settings.ai_diagnostics_max_file_bytes:
            files[-1].unlink(missing_ok=True)
            for source, target in reversed(list(zip(files[:-1], files[1:]))):
                if source.exists(): os.replace(source, target)
        fd = os.open(path, os.O_CREAT | os.O_APPEND | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, 'ab', closefd=False) as stream:
                stream.write(encoded)
        finally: os.close(fd)
    finally: os.close(lock)


def record(event, *, settings=None, content=None, **data):
    try:
        context = _context.get()
        settings = settings or (context['settings'] if context else get_settings())
        if not settings.ai_diagnostics_enabled: return
        entry = {'timeUTC': datetime.now(timezone.utc).isoformat(), 'event': event,
                 'traceId': context['traceId'] if context else data.get('callId'), **data}
        if context: entry['path'] = context['path']
        if content is not None:
            safe = json.dumps(_clean(content, settings), ensure_ascii=False)
            entry['contentBytes'] = len(safe.encode())
            entry['contentSha256'] = hashlib.sha256(safe.encode()).hexdigest()
            entry['contentCaptured'] = settings.ai_diagnostics_capture_content
            if settings.ai_diagnostics_capture_content:
                limit = settings.ai_diagnostics_max_content_characters
                entry['contentTruncated'] = len(safe) > limit
                entry['content'] = json.loads(safe) if len(safe) <= limit else safe[:limit]
        _write(settings, _clean(entry, settings))
    except Exception as error:
        # Logging must not break teaching, reserve quota or trigger paid retries.
        logger.warning('AI diagnostics write unavailable (%s)', type(error).__name__)


@contextmanager
def request_context(settings, path):
    context = {'settings': settings, 'path': path, 'traceId': uuid.uuid4().hex}
    token = _context.set(context)
    try: yield context['traceId']
    finally: _context.reset(token)


def api_error(code, message, status):
    if _context.get(): record('api.error', code=code, message=message, status=status)


def model_call(kind, model, payload, invoke, *, settings=None):
    """Wrap exactly one existing SDK call; no new requests or automatic retries."""
    call_id = uuid.uuid4().hex
    record('model.request', settings=settings, callId=call_id, kind=kind, model=model, content=payload)
    started = time.monotonic()
    try:
        response = invoke()
    except Exception as error:
        from pydantic import ValidationError
        issues = error.errors(include_input=False, include_url=False) if isinstance(error, ValidationError) else None
        record('model.error', settings=settings, callId=call_id, kind=kind, model=model,
               exceptionType=type(error).__name__, code=getattr(error, 'code', None), content={'schemaIssues': issues} if issues else None,
               latencyMs=round((time.monotonic()-started)*1000))
        raise
    try:
        parsed = getattr(response, 'output_parsed', None)
        output = {'responseId': getattr(response, 'id', None), 'status': getattr(response, 'status', None)}
        if parsed is not None:
            output['output'] = parsed.model_dump(mode='json') if hasattr(parsed, 'model_dump') else parsed
        if kind == 'responses' and parsed is None:
            # Include refusal/incomplete text if parsing succeeded without a schema.
            output['outputText'] = getattr(response, 'output_text', None)
            output['incompleteReason'] = getattr(getattr(response, 'incomplete_details', None), 'reason', None)
        usage = getattr(response, 'usage', None)
        output['usage'] = {k: getattr(usage, k, None) for k in ('input_tokens','output_tokens','total_tokens','prompt_tokens')}
        if kind in {'images','embeddings'}:
            output['resultCount'] = len(getattr(response, 'data', []) or [])
        # No image bytes, embedding vectors, Realtime secret values or raw headers.
        record('model.response', settings=settings, callId=call_id, kind=kind, model=model,
               latencyMs=round((time.monotonic()-started)*1000), content=output)
    except Exception:
        record('model.response', settings=settings, callId=call_id, kind=kind, model=model, summaryUnavailable=True)
    return response
