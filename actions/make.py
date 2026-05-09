import os
from pathlib import Path

from actions.base import BaseAction
from process import shell


class Action(BaseAction):
    args: str = ""

    async def run(self, cwd: Path, env: dict[str, str]) -> None:
        await shell(f"make -j{os.cpu_count()} {self.args}", cwd=cwd, env=env)
