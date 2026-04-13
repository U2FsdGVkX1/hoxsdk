import asyncio
import importlib
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Action(ABC):
    @abstractmethod
    async def run(self, cwd: Path, env: Dict[str, str]) -> None:
        raise NotImplementedError()

    @staticmethod
    def create(action_config: dict) -> "Action":
        use = action_config.get("use")
        if not use:
            raise ValueError("Action must have 'use' field")

        module = importlib.import_module(f"actions.{use}")
        action_class = module.__dict__.get(f"{use.capitalize()}Action")
        if not action_class:
            raise ValueError(f"Action class '{use.capitalize()}Action' not found")

        action_kwargs = {
            key: value
            for key, value in action_config.items()
            if key != "use"
        }
        return action_class(**action_kwargs)


class Target:
    requires: List[str]
    depends: List[str]
    env: Dict[str, str]
    actions: List[Action]
    result: List[str]

    def __init__(self, target_config: dict) -> None:
        self.requires = target_config.get("requires", [])
        self.depends = target_config.get("depends", [])
        self.env = target_config.get("env", {})
        self.actions = [
            Action.create(action)
            for action in target_config.get("actions", [])
        ]
        self.result = target_config.get("result", [])


async def shell(
    cmd: str,
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
) -> Tuple[asyncio.subprocess.Process, bytes, bytes]:
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
