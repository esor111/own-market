"""
Shared atomic write helpers for generated JSON and markdown artifacts.
"""
import json
import os
import tempfile
import time


def _atomic_write_text(path, text):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".tmp_", dir=directory, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        last_error = None
        for _ in range(5):
            try:
                os.replace(temp_path, path)
                last_error = None
                break
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.1)
        if last_error is not None:
            raise last_error
    except Exception:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        finally:
            raise


def save_json_atomic(path, payload):
    _atomic_write_text(path, json.dumps(payload, indent=2))


def save_text_atomic(path, payload):
    _atomic_write_text(path, payload)
