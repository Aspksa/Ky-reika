"""Process telemetry; unavailable platform counters remain null."""
import os
import time
import threading
from pathlib import Path
from .database import DB_PATH

_started=time.monotonic()
_lock=threading.Lock()
_previous=None

def report(path=DB_PATH):
    global _previous
    with _lock:
        wall,cpu=time.monotonic(),time.process_time()
        percent=None
        if _previous and wall>_previous[0]:
            percent=round(100*(cpu-_previous[1])/(wall-_previous[0]),2)
        _previous=(wall,cpu)
    rss=None
    try:
        import psutil
        rss=psutil.Process().memory_info().rss
    except (ImportError,OSError):
        try:
            for line in Path("/proc/self/status").read_text().splitlines():
                if line.startswith("VmRSS:"):
                    rss=int(line.split()[1])*1024
                    break
        except (OSError,ValueError,IndexError):
            pass
    sizes={}
    for name,suffix in (("database",""),("wal","-wal"),("shm","-shm")):
        try:
            sizes[name]=Path(str(path)+suffix).stat().st_size
        except FileNotFoundError:
            sizes[name]=0
        except OSError:
            sizes[name]=None
    return {"cpu_percent":percent,"rss_bytes":rss,"uptime_seconds":int(wall-_started),
            "database_bytes":sizes,"logical_cpus":os.cpu_count(),
            "cloud_configured":all(bool(os.environ.get(k)) for k in ("CLOUD_API_BASE","CLOUD_API_KEY","CLOUD_MODEL"))}
