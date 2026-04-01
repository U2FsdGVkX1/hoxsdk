from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from sdkhelper import Action, shell

@dataclass
class GitAction(Action):
    src: str
    path: str = "."
    branch: Optional[str] = None
    hash: Optional[str] = None
    async def run(self, cwd: Path, env: dict) -> None:
        cmd = "git clone"
        if not self.hash:
            cmd += " --depth=1"
        if self.branch:
            cmd += f" -b {self.branch}"
        cmd += f" {self.src} {self.path}"
        await shell(cmd, cwd=cwd, env=env)

        if self.hash:
            repo_dir = cwd / self.path
            checkout_cmd = f"git checkout {self.hash}"
            await shell(checkout_cmd, cwd=repo_dir, env=env)
