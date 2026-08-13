"""CI compatibility shim for the V52 historical harness.

Python may return bytes in TimeoutExpired.stdout even when subprocess.run(text=True).
Normalize that one edge case into an ordinary CompletedProcess so the frozen
experiment records an infrastructure/test timeout instead of crashing.
"""
import subprocess

_original_run = subprocess.run

def _run(*args, **kwargs):
    try:
        return _original_run(*args, **kwargs)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or b""
        err = exc.stderr or b""
        if isinstance(out, bytes):
            out = out.decode(errors="replace")
        if isinstance(err, bytes):
            err = err.decode(errors="replace")
        return subprocess.CompletedProcess(exc.cmd, 124, stdout=out + err, stderr=None)

subprocess.run = _run
