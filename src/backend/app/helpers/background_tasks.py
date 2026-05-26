"""Fire-and-forget asyncio task helper.

The asyncio event loop only holds weak references to tasks created with
``asyncio.create_task``. If the caller does not retain the returned ``Task``,
it can be garbage-collected mid-execution - interrupting cleanup paths such
as ``async with`` for DB connections and leaking transactions / locks.

This module keeps a module-level strong reference until the task completes.
"""

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

log = logging.getLogger(__name__)

_BG_TASKS: set[asyncio.Task[Any]] = set()


def spawn(coro: Coroutine[Any, Any, Any], *, name: str | None = None) -> asyncio.Task:
    """Schedule ``coro`` on the running loop and retain a strong reference.

    Use this instead of ``asyncio.create_task`` for any "do this after the
    response" work that must not be GC'd mid-flight.
    """
    task = asyncio.create_task(coro, name=name)
    _BG_TASKS.add(task)
    task.add_done_callback(_on_done)
    return task


def _on_done(task: asyncio.Task[Any]) -> None:
    _BG_TASKS.discard(task)
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        log.exception(
            "Background task %s raised an unhandled exception",
            task.get_name(),
            exc_info=exc,
        )
