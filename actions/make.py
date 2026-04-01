import os
from pathlib import Path
from dataclasses import dataclass

from sdkhelper import Action, shell

@dataclass
class MakeAction(Action):
    args: str = ""
    async def run(self, cwd: Path, env: dict) -> None:
        cmd = f"make -j{os.cpu_count()} {self.args}"
        await shell(cmd, cwd=cwd, env=env)
