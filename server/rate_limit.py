"""Shared slowapi limiter for mutation endpoints.

The single module-level Limiter is attached to ``app.state.limiter`` by
create_app() and imported by routes for the ``@limiter.limit(...)``
decorators. slowapi enforces through the decorator instance's in-memory
storage, so create_app() calls ``limiter.reset()`` — every app (including
test apps) starts with a clean slate.

Only non-GET endpoints are decorated; GET endpoints stay unlimited so bare
test apps without ``app.state.limiter`` keep working.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
