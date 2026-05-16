import shutil
from pathlib import Path

from actions.base import BaseAction


class Action(BaseAction):
    src: Path
    dest: Path

    async def run(self, cwd: Path, env: dict[str, str]) -> None:
        src = cwd / self.src
        dst = cwd / self.dest
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
