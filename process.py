import asyncio
import os
import sys
from pathlib import Path
from typing import Optional


async def shell(
    cmd: str,
    cwd: Optional[Path] = None,
    env: Optional[dict[str, str]] = None,
) -> tuple[asyncio.subprocess.Process, bytes, bytes]:
    def _log_file() -> Path:
        import main

        task = asyncio.current_task()
        task_name = task.get_name() if task else "main"
        log_file = Path("logs") / main.args.board / f"{task_name}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        return log_file

    process = await asyncio.create_subprocess_shell(
        cmd,
        cwd=cwd,
        env={**os.environ, **({} if env is None else env)},
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=True,
    )

    with _log_file().open("ab") as log:
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
    if process.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {process.returncode}: {cmd}\n"
            f"{stderr_data.decode(errors='replace')}"
        )
    return process, stdout_data, stderr_data
