from pathlib import Path

from pydantic import Field

from actions.base import BaseAction
from process import shell


class Action(BaseAction):
    src: str
    path: str = "."
    branch: str | None = None
    commit_hash: str | None = Field(default=None, alias="hash")

    async def run(self, cwd: Path, env: dict[str, str]) -> None:
        cmd = "git clone"
        if not self.commit_hash:
            cmd += " --depth=1"
        if self.branch:
            cmd += f" -b {self.branch}"
        cmd += f" {self.src} {self.path}"
        await shell(cmd, cwd=cwd, env=env)

        if self.commit_hash:
            repo_dir = cwd / self.path
            await shell(f"git checkout {self.commit_hash}", cwd=repo_dir, env=env)
