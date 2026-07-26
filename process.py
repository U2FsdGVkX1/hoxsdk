import asyncio
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path


_command_log: ContextVar[Path | None] = ContextVar("command_log", default=None)


@contextmanager
def command_log(path: Path) -> Iterator[None]:
    token = _command_log.set(path.resolve())
    try:
        yield
    finally:
        _command_log.reset(token)


async def shell(
    cmd: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> tuple[asyncio.subprocess.Process, bytes, bytes]:
    log_file = _command_log.get()
    if log_file is None:
        raise RuntimeError("Command log context is not configured")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    process = await asyncio.create_subprocess_shell(
        cmd,
        cwd=cwd,
        env=os.environ | (env or {}),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=True,
    )

    try:
        with log_file.open("ab") as log:
            log.write(f"$ {cmd}\n".encode())

            async def _pump(stream, out) -> bytes:
                data = bytearray()
                while chunk := await stream.read(4096):
                    data.extend(chunk)
                    out.write(chunk.decode(errors="replace"))
                    out.flush()
                    log.write(chunk)
                return bytes(data)

            stdout_data, stderr_data = await asyncio.gather(
                _pump(process.stdout, sys.stdout),
                _pump(process.stderr, sys.stderr),
            )

        await process.wait()
    except asyncio.CancelledError:
        if process.returncode is None:
            process.kill()
        raise
    if process.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {process.returncode}: {cmd}\n"
            f"{stderr_data.decode(errors='replace')}"
        )
    return process, stdout_data, stderr_data
