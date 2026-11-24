"""Consistent local SQLite snapshots; restoration is an offline operator action."""
import os
import sqlite3
from pathlib import Path
from .database import DB_PATH, connect

def refresh(path=DB_PATH):
    path=Path(path)
    folder=path.parent/(path.name+".backups")
    folder.mkdir(mode=0o700,exist_ok=True)
    target=folder/"latest.sqlite3"
    temp=folder/"pending.sqlite3"
    with connect(path) as source:
        dest=sqlite3.connect(temp)
        try:
            source.backup(dest)
            if dest.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
                raise RuntimeError("Invalid backup")
        finally:
            dest.close()
    os.chmod(temp,0o600)
    os.replace(temp,target)
    return target
