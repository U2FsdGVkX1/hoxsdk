import os
from pathlib import Path
from dataclasses import dataclass, field
from fmhelper import Action, shell

@dataclass
class MakeAction(Action):
    args: str = ""
    async def run(self, cwd: Path, env: dict) -> None:
        cmd = f"make -j{os.cpu_count()} {self.args}"
        process, _, stderr = await shell(cmd, cwd=cwd, env=env)
        if process.returncode != 0:
            raise RuntimeError(f"Make failed:\n{stderr.decode()}")