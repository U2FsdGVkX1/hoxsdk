from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from fmhelper import Action, shell

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
        process, _, stderr = await shell(cmd, cwd=cwd, env=env)
        if process.returncode != 0:
            raise RuntimeError(f"Git clone failed:\n{stderr.decode()}")

        if self.hash:
            repo_dir = cwd / self.path
            checkout_cmd = f"git checkout {self.hash}"
            process, _, stderr = await shell(checkout_cmd, cwd=repo_dir, env=env)
            if process.returncode != 0:
                raise RuntimeError(f"Git checkout failed:\n{stderr.decode()}")
