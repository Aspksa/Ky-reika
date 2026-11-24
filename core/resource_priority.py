"""Cooperative priority: running background work is never interrupted."""
from contextlib import contextmanager
from threading import Condition

_condition=Condition()
_active=0

@contextmanager
def foreground():
    global _active
    with _condition:
        _active+=1
    try:
        yield
    finally:
        with _condition:
            _active-=1
            _condition.notify_all()

def wait_for_idle():
    with _condition:
        _condition.wait_for(lambda: _active==0)
