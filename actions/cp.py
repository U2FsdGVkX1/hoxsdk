import shutil
from pathlib import Path
from dataclasses import dataclass, field
from fmhelper import Action, shell

@dataclass
class CpAction(Action):
    src: str
    dest: str
    async def run(self, cwd: Path, env: dict) -> None:
        src = cwd / self.src
        dst = cwd / self.dest
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)