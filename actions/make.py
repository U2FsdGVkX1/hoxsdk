import os
from pathlib import Path

from process import shell


async def run(action: dict, cwd: Path, env: dict[str, str]) -> None:
    args = action.get("args", "")
    await shell(f"make -j{os.cpu_count()} {args}", cwd=cwd, env=env)
