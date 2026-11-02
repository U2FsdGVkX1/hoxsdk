from collections.abc import Sequence
from pathlib import Path

from pydantic import Field

from actions.base import BaseAction, PathArg
from process import shell


class Action(BaseAction):
    patches: Sequence[PathArg] = Field(default_factory=tuple)
    gitam: bool = False

    async def run(self, cwd: Path, env: dict[str, str]) -> None:
        for patch in self.patches:
            if self.gitam:
                await shell(f"git am {patch}", cwd=cwd, env=env)
            else:
                await shell(f"patch -p1 < {patch}", cwd=cwd, env=env)
